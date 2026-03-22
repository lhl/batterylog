import os
import shlex
import shutil
import sys
import tempfile
from pathlib import Path

from batterylog.db import connect_database
from batterylog.paths import SYSTEM_CONFIG_PATH

SYSTEM_DEFAULT_DB_PATH = Path("/var/lib/batterylog/batterylog.db")
SYSTEM_HOOK_PATH = Path("/usr/lib/systemd/system-sleep/batterylog")
UV_EPHEMERAL_MARKER = "/.cache/uv/archive-"


class HookInstallError(RuntimeError):
    pass


def install_hook(
    db_path: Path | None = None,
    *,
    hook_command: str | None = None,
    system_config_path: Path = SYSTEM_CONFIG_PATH,
    system_hook_path: Path = SYSTEM_HOOK_PATH,
) -> int:
    active_db_path = (db_path or SYSTEM_DEFAULT_DB_PATH).expanduser()
    command_path = resolve_hook_command_path(hook_command)
    ensure_stable_hook_command(command_path)

    initialize_hook_database(active_db_path)
    install_managed_files(
        system_config_path,
        render_config(active_db_path),
        system_hook_path,
        render_hook(command_path, active_db_path),
    )

    print(f"Installed hook at {system_hook_path}")
    print(f"Configured database at {active_db_path}")
    return 0


def uninstall_hook(
    *,
    system_config_path: Path = SYSTEM_CONFIG_PATH,
    system_hook_path: Path = SYSTEM_HOOK_PATH,
) -> int:
    hook_removed = unlink_if_exists(system_hook_path)
    config_removed = unlink_if_exists(system_config_path)

    print(status_message("hook", system_hook_path, hook_removed))
    print(status_message("config", system_config_path, config_removed))
    return 0


def resolve_hook_command_path(hook_command: str | None = None) -> Path:
    if hook_command:
        return validate_command_path(Path(hook_command).expanduser().resolve())

    argv0 = sys.argv[0]
    if not argv0:
        raise HookInstallError("Could not determine the current batterylog command path.")

    candidate = Path(argv0).expanduser()
    if candidate.is_absolute() or "/" in argv0:
        return validate_command_path(candidate.resolve())

    resolved = shutil.which(argv0)
    if resolved is None:
        raise HookInstallError(
            f"Could not resolve the installed command path for {argv0!r}. "
            "Use --hook-command with an absolute path."
        )

    return validate_command_path(Path(resolved).resolve())


def validate_command_path(command_path: Path) -> Path:
    if not command_path.exists():
        raise HookInstallError(f"Hook command path does not exist: {command_path}")

    if not command_path.is_file():
        raise HookInstallError(f"Hook command path is not a file: {command_path}")

    if not os.access(command_path, os.X_OK):
        raise HookInstallError(f"Hook command path is not executable: {command_path}")

    return command_path


def ensure_stable_hook_command(command_path: Path) -> None:
    if UV_EPHEMERAL_MARKER in str(command_path):
        raise HookInstallError(
            "Refusing to install a persistent system hook from a uvx ephemeral path. "
            "Install batterylog with pip, uv tool install, pipx, or use INSTALL.sh."
        )


def initialize_hook_database(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.parent.chmod(0o755)
    connection = connect_database(db_path)
    connection.close()
    if db_path.exists():
        db_path.chmod(0o644)


def install_managed_files(config_path: Path, config_content: str, hook_path: Path, hook_content: str) -> None:
    config_snapshot = snapshot_file(config_path)
    hook_snapshot = snapshot_file(hook_path)

    try:
        write_text_file_atomically(hook_path, hook_content, mode=0o755)
        write_text_file_atomically(config_path, config_content, mode=0o644)
    except OSError as exc:
        rollback_error = rollback_managed_files(
            config_path,
            config_snapshot,
            hook_path,
            hook_snapshot,
        )
        if rollback_error is not None:
            raise HookInstallError(
                f"Failed to install managed hook files: {exc}. Rollback also failed: {rollback_error}"
            ) from exc
        raise HookInstallError(f"Failed to install managed hook files: {exc}") from exc


def rollback_managed_files(
    config_path: Path,
    config_snapshot: tuple[str, int] | None,
    hook_path: Path,
    hook_snapshot: tuple[str, int] | None,
) -> OSError | None:
    errors = []

    for path, snapshot in ((hook_path, hook_snapshot), (config_path, config_snapshot)):
        try:
            restore_file(path, snapshot)
        except OSError as exc:
            errors.append(exc)

    return errors[0] if errors else None


def render_config(db_path: Path) -> str:
    escaped_path = str(db_path).replace("\\", "\\\\").replace('"', '\\"')
    return f'db_path = "{escaped_path}"\n'


def render_hook(command_path: Path, db_path: Path) -> str:
    quoted_command = shlex.quote(str(command_path))
    quoted_db_path = shlex.quote(str(db_path))

    return """#!/bin/sh

case "$1" in
    pre)  {command} --db {db_path} suspend ;;
    post) {command} --db {db_path} resume ;;
esac
""".format(command=quoted_command, db_path=quoted_db_path)


def write_text_file_atomically(path: Path, content: str, *, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.parent.chmod(0o755)

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as handle:
            handle.write(content)
            temp_path = Path(handle.name)

        temp_path.chmod(mode)
        temp_path.replace(path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def snapshot_file(path: Path) -> tuple[str, int] | None:
    if not path.exists():
        return None

    return (path.read_text(), path.stat().st_mode & 0o777)


def restore_file(path: Path, snapshot: tuple[str, int] | None) -> None:
    if snapshot is None:
        unlink_if_exists(path)
        return

    content, mode = snapshot
    write_text_file_atomically(path, content, mode=mode)


def unlink_if_exists(path: Path) -> bool:
    try:
        path.unlink()
        return True
    except FileNotFoundError:
        return False


def status_message(kind: str, path: Path, removed: bool) -> str:
    if removed:
        return f"Removed {kind} at {path}"

    return f"No {kind} installed at {path}"
