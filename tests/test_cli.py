from pathlib import Path

from batterylog.cli import main


def test_cli_install_hook_dispatches_to_hook_manager(monkeypatch, tmp_path):
    captured = {}

    def fake_install_hook(db_path, *, hook_command=None):
        captured["db_path"] = db_path
        captured["hook_command"] = hook_command
        return 0

    monkeypatch.setattr("batterylog.cli.install_hook", fake_install_hook)

    result = main(
        [
            "install-hook",
            "--db",
            str(tmp_path / "batterylog.db"),
            "--hook-command",
            str(tmp_path / "batterylog"),
        ]
    )

    assert result == 0
    assert captured["db_path"] == Path(tmp_path / "batterylog.db")
    assert captured["hook_command"] == str(tmp_path / "batterylog")


def test_cli_uninstall_hook_dispatches_to_hook_manager(monkeypatch):
    called = {"count": 0}

    def fake_uninstall_hook():
        called["count"] += 1
        return 0

    monkeypatch.setattr("batterylog.cli.uninstall_hook", fake_uninstall_hook)

    assert main(["uninstall-hook"]) == 0
    assert called["count"] == 1
