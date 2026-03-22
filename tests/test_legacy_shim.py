import runpy
import shutil
import sqlite3
import sys
from pathlib import Path

import pytest

from batterylog.power import BatterySnapshot


ROOT = Path(__file__).resolve().parents[1]


def create_legacy_tree(tmp_path: Path) -> Path:
    legacy_dir = tmp_path / "opt" / "batterylog"
    legacy_dir.mkdir(parents=True)
    shutil.copy2(ROOT / "batterylog.py", legacy_dir / "batterylog.py")
    shutil.copy2(ROOT / "pyproject.toml", legacy_dir / "pyproject.toml")
    shutil.copy2(ROOT / "schema.sql", legacy_dir / "schema.sql")
    shutil.copytree(ROOT / "src", legacy_dir / "src")
    return legacy_dir


def run_legacy_script(script_path: Path, argv: list[str], monkeypatch) -> int:
    monkeypatch.setattr(sys, "argv", [str(script_path), *argv])
    with pytest.raises(SystemExit) as excinfo:
        runpy.run_path(str(script_path), run_name="__main__")
    return int(excinfo.value.code)


def test_legacy_batterylog_py_keeps_suspend_resume_and_report_flow(tmp_path, monkeypatch, capsys):
    legacy_dir = create_legacy_tree(tmp_path)
    script_path = legacy_dir / "batterylog.py"

    snapshots = iter(
        [
            BatterySnapshot(
                name="BAT0",
                cycle_count=100,
                charge_now=50_000_000,
                current_now=0,
                voltage_now=1_000_000,
                voltage_min_design=1_000_000,
                battery_status="Discharging",
                line_power_name="AC",
                line_power_online=0,
            ),
            BatterySnapshot(
                name="BAT0",
                cycle_count=100,
                charge_now=49_000_000,
                current_now=0,
                voltage_now=1_000_000,
                voltage_min_design=1_000_000,
                battery_status="Discharging",
                line_power_name="AC",
                line_power_online=0,
            ),
        ]
    )
    event_times = iter([100, 200])

    monkeypatch.setattr("batterylog.core.read_battery_snapshot", lambda: next(snapshots))
    monkeypatch.setattr("batterylog.core.read_charge_full", lambda battery_name: 50_000_000)
    monkeypatch.setattr("batterylog.core.time.time", lambda: next(event_times))
    monkeypatch.setattr("batterylog.paths.read_db_path_from_config", lambda config_path: None)

    assert run_legacy_script(script_path, ["suspend"], monkeypatch) == 0
    assert run_legacy_script(script_path, ["resume"], monkeypatch) == 0
    capsys.readouterr()

    assert run_legacy_script(script_path, [], monkeypatch) == 0

    db_path = legacy_dir / "batterylog.db"
    assert db_path.exists()

    connection = sqlite3.connect(str(db_path))
    try:
        rows = connection.execute(
            """
            SELECT event, battery_status, line_power_name, line_power_online
            FROM log
            ORDER BY time ASC
            """
        ).fetchall()
    finally:
        connection.close()

    assert [row[0] for row in rows] == ["suspend", "resume"]
    assert rows[0][1:] == ("Discharging", "AC", 0)
    assert rows[1][1:] == ("Discharging", "AC", 0)

    output = capsys.readouterr().out
    assert "Slept for 0.03 hours" in output
    assert "Used 1.00 Wh, an average rate of 36.00 W" in output
