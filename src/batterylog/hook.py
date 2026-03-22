import os
import shlex
import shutil
import sys
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

    write_config(system_config_path, active_db_path)
    initialize_hook_database(active_db_path)
    write_hook(system_hook_path, command_path, active_db_path)

    print(f"Installed hook at {system_hook_path}")
    print(f"Configured database at {active_db_path}")
    return 0


def uninstall_hook(
    *,
    system_config_path: Path = SYSTEM_CONFIG_PATH,
    system_hook_path: Path = SYSTEM_HOOK_PATH,
) -> int:
    remove_file_if_exists(system_hook_path)
    remove_file_if_exists(system_config_path)

    print(f"Removed hook at {system_hook_path}")
    print(f"Removed config at {system_config_path}")
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
    ensure_directory(db_path.parent, mode=0o755)
    connection = connect_database(db_path)
    connection.close()
    if db_path.exists():
        db_path.chmod(0o644)


def write_config(config_path: Path, db_path: Path) -> None:
    ensure_directory(config_path.parent, mode=0o755)
    content = render_config(db_path)
    write_text_file(config_path, content, mode=0o644)


def write_hook(hook_path: Path, command_path: Path, db_path: Path) -> None:
    ensure_directory(hook_path.parent, mode=0o755)
    content = render_hook(command_path, db_path)
    write_text_file(hook_path, content, mode=0o755)


def ensure_directory(path: Path, *, mode: int) -> None:
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(mode)


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


def write_text_file(path: Path, content: str, *, mode: int) -> None:
    path.write_text(content)
    path.chmod(mode)


def remove_file_if_exists(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass
