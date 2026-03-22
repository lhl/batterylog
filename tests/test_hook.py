import sqlite3

import pytest

import batterylog.hook as hook_module
from batterylog.hook import (
    HookInstallError,
    install_hook,
    uninstall_hook,
)


def make_executable(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\nexit 0\n")
    path.chmod(0o755)
    return path


def test_install_hook_writes_managed_files(tmp_path):
    command_path = make_executable(tmp_path / "bin" / "batterylog")
    db_path = tmp_path / "var" / "lib" / "batterylog" / "batterylog.db"
    config_path = tmp_path / "etc" / "batterylog" / "config.toml"
    hook_path = tmp_path / "usr" / "lib" / "systemd" / "system-sleep" / "batterylog"

    result = install_hook(
        db_path,
        hook_command=str(command_path),
        system_config_path=config_path,
        system_hook_path=hook_path,
    )

    assert result == 0
    assert config_path.read_text() == f'db_path = "{db_path}"\n'
    assert db_path.exists()
    with sqlite3.connect(db_path) as connection:
        assert connection.execute("select name from sqlite_master").fetchall()

    hook_text = hook_path.read_text()
    assert f"{command_path} --db {db_path} suspend" in hook_text
    assert f"{command_path} --db {db_path} resume" in hook_text

    assert config_path.stat().st_mode & 0o777 == 0o644
    assert db_path.stat().st_mode & 0o777 == 0o644
    assert hook_path.stat().st_mode & 0o777 == 0o755


def test_uninstall_hook_is_idempotent_and_keeps_db(tmp_path):
    command_path = make_executable(tmp_path / "bin" / "batterylog")
    db_path = tmp_path / "var" / "lib" / "batterylog" / "batterylog.db"
    config_path = tmp_path / "etc" / "batterylog" / "config.toml"
    hook_path = tmp_path / "usr" / "lib" / "systemd" / "system-sleep" / "batterylog"

    install_hook(
        db_path,
        hook_command=str(command_path),
        system_config_path=config_path,
        system_hook_path=hook_path,
    )

    assert uninstall_hook(system_config_path=config_path, system_hook_path=hook_path) == 0
    assert uninstall_hook(system_config_path=config_path, system_hook_path=hook_path) == 0
    assert not config_path.exists()
    assert not hook_path.exists()
    assert db_path.exists()


def test_install_hook_uses_system_default_db_path(tmp_path, monkeypatch):
    command_path = make_executable(tmp_path / "bin" / "batterylog")
    default_db_path = tmp_path / "var" / "lib" / "batterylog" / "batterylog.db"
    config_path = tmp_path / "etc" / "batterylog" / "config.toml"
    hook_path = tmp_path / "usr" / "lib" / "systemd" / "system-sleep" / "batterylog"

    monkeypatch.setattr("batterylog.hook.SYSTEM_DEFAULT_DB_PATH", default_db_path)

    install_hook(
        hook_command=str(command_path),
        system_config_path=config_path,
        system_hook_path=hook_path,
    )

    assert config_path.read_text() == f'db_path = "{default_db_path}"\n'
    assert default_db_path.exists()


def test_install_hook_rejects_uvx_ephemeral_paths(tmp_path):
    command_path = make_executable(tmp_path / ".cache" / "uv" / "archive-v0" / "tool" / "batterylog")
    db_path = tmp_path / "var" / "lib" / "batterylog" / "batterylog.db"
    config_path = tmp_path / "etc" / "batterylog" / "config.toml"
    hook_path = tmp_path / "usr" / "lib" / "systemd" / "system-sleep" / "batterylog"

    with pytest.raises(HookInstallError):
        install_hook(
            db_path,
            hook_command=str(command_path),
            system_config_path=config_path,
            system_hook_path=hook_path,
        )

    assert not config_path.exists()
    assert not hook_path.exists()
    assert not db_path.exists()


def test_install_hook_restores_previous_files_on_partial_failure(tmp_path, monkeypatch):
    command_path = make_executable(tmp_path / "bin" / "batterylog")
    db_path = tmp_path / "var" / "lib" / "batterylog" / "batterylog.db"
    config_path = tmp_path / "etc" / "batterylog" / "config.toml"
    hook_path = tmp_path / "usr" / "lib" / "systemd" / "system-sleep" / "batterylog"

    config_path.parent.mkdir(parents=True, exist_ok=True)
    hook_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text('db_path = "/old/batterylog.db"\n')
    config_path.chmod(0o600)
    hook_path.write_text("#!/bin/sh\nold hook\n")
    hook_path.chmod(0o700)

    original_write = hook_module.write_text_file_atomically
    calls = {"count": 0}

    def flaky_write(path, content, *, mode):
        calls["count"] += 1
        if calls["count"] == 2:
            raise OSError("simulated write failure")
        return original_write(path, content, mode=mode)

    monkeypatch.setattr("batterylog.hook.write_text_file_atomically", flaky_write)

    with pytest.raises(HookInstallError, match="Failed to install managed hook files"):
        install_hook(
            db_path,
            hook_command=str(command_path),
            system_config_path=config_path,
            system_hook_path=hook_path,
        )

    assert config_path.read_text() == 'db_path = "/old/batterylog.db"\n'
    assert config_path.stat().st_mode & 0o777 == 0o600
    assert hook_path.read_text() == "#!/bin/sh\nold hook\n"
    assert hook_path.stat().st_mode & 0o777 == 0o700


def test_uninstall_hook_reports_when_nothing_is_installed(tmp_path, capsys):
    config_path = tmp_path / "etc" / "batterylog" / "config.toml"
    hook_path = tmp_path / "usr" / "lib" / "systemd" / "system-sleep" / "batterylog"

    assert uninstall_hook(system_config_path=config_path, system_hook_path=hook_path) == 0

    lines = capsys.readouterr().out.strip().splitlines()
    assert lines == [
        f"No hook installed at {hook_path}",
        f"No config installed at {config_path}",
    ]
