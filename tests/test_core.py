from batterylog.core import NO_CAPACITY_MESSAGE, NO_DATA_MESSAGE, report_last_cycle
from batterylog.db import connect_database


WH = 1_000_000_000_000
VOLTAGE_MIN_DESIGN = 1_000_000
CHARGE_FULL = 50_000_000


def insert_log_row(db_path, *, time_value, event, energy_min_wh):
    connection = connect_database(db_path)
    connection.execute(
        "INSERT INTO log VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            time_value,
            "BAT0",
            event,
            100,
            0,
            0,
            0,
            VOLTAGE_MIN_DESIGN,
            energy_min_wh * WH,
            energy_min_wh * WH,
            0,
            0,
        ),
    )
    connection.commit()
    connection.close()


def test_report_last_cycle_uses_latest_complete_pair(tmp_path, monkeypatch, capsys):
    db_path = tmp_path / "batterylog.db"

    insert_log_row(db_path, time_value=100, event="suspend", energy_min_wh=50)
    insert_log_row(db_path, time_value=200, event="resume", energy_min_wh=49)
    insert_log_row(db_path, time_value=300, event="suspend", energy_min_wh=48)

    monkeypatch.setattr("batterylog.core.read_charge_full", lambda battery_name: CHARGE_FULL)

    assert report_last_cycle(db_path) == 0

    output = capsys.readouterr().out
    assert "Slept for 0.03 hours" in output
    assert "Used 1.00 Wh, an average rate of 36.00 W" in output
    assert "your battery would be empty" in output


def test_report_last_cycle_handles_missing_preceding_suspend(tmp_path, monkeypatch, capsys):
    db_path = tmp_path / "batterylog.db"

    insert_log_row(db_path, time_value=200, event="resume", energy_min_wh=49)
    insert_log_row(db_path, time_value=300, event="suspend", energy_min_wh=48)

    monkeypatch.setattr("batterylog.core.read_charge_full", lambda battery_name: CHARGE_FULL)

    assert report_last_cycle(db_path) == 0
    assert capsys.readouterr().out.strip() == NO_DATA_MESSAGE


def test_report_last_cycle_handles_zero_full_capacity_metadata(tmp_path, monkeypatch, capsys):
    db_path = tmp_path / "batterylog.db"

    insert_log_row(db_path, time_value=100, event="suspend", energy_min_wh=50)
    insert_log_row(db_path, time_value=200, event="resume", energy_min_wh=49)

    monkeypatch.setattr("batterylog.core.read_charge_full", lambda battery_name: 0)

    assert report_last_cycle(db_path) == 0

    output = capsys.readouterr().out
    assert "Slept for 0.03 hours" in output
    assert "Used 1.00 Wh, an average rate of 36.00 W" in output
    assert NO_CAPACITY_MESSAGE in output
