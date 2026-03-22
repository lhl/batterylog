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


def test_cli_migrate_db_dispatches_to_migration_manager(monkeypatch, tmp_path):
    captured = {}

    def fake_migrate_database_path(source_path, destination_path):
        captured["source"] = source_path
        captured["destination"] = destination_path
        return 0

    monkeypatch.setattr("batterylog.cli.migrate_database_path", fake_migrate_database_path)

    result = main(
        [
            "migrate-db",
            "--from",
            str(tmp_path / "source.db"),
            "--to",
            str(tmp_path / "destination.db"),
        ]
    )

    assert result == 0
    assert captured["source"] == Path(tmp_path / "source.db")
    assert captured["destination"] == Path(tmp_path / "destination.db")


def test_cli_history_dispatches_to_history_report(monkeypatch, tmp_path):
    captured = {}

    def fake_report_history(db_path, *, limit, discharging_only):
        captured["db_path"] = db_path
        captured["limit"] = limit
        captured["discharging_only"] = discharging_only
        return 0

    monkeypatch.setattr("batterylog.cli.report_history", fake_report_history)

    result = main(
        [
            "history",
            "--db",
            str(tmp_path / "batterylog.db"),
            "--limit",
            "5",
            "--discharging-only",
        ]
    )

    assert result == 0
    assert captured["db_path"] == Path(tmp_path / "batterylog.db")
    assert captured["limit"] == 5
    assert captured["discharging_only"] is True


def test_cli_summary_dispatches_to_summary_report(monkeypatch, tmp_path):
    captured = {}

    def fake_report_summary(db_path, *, limit, discharging_only):
        captured["db_path"] = db_path
        captured["limit"] = limit
        captured["discharging_only"] = discharging_only
        return 0

    monkeypatch.setattr("batterylog.cli.report_summary", fake_report_summary)

    result = main(
        [
            "summary",
            "--db",
            str(tmp_path / "batterylog.db"),
            "--limit",
            "7",
        ]
    )

    assert result == 0
    assert captured["db_path"] == Path(tmp_path / "batterylog.db")
    assert captured["limit"] == 7
    assert captured["discharging_only"] is False
