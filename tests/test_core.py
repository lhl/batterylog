from batterylog.core import (
    NO_CAPACITY_MESSAGE,
    NO_DATA_MESSAGE,
    log_event,
    report_history,
    report_last_cycle,
    report_summary,
)
from batterylog.db import connect_database
from batterylog.power import BatterySnapshot


WH = 1_000_000_000_000
VOLTAGE_MIN_DESIGN = 1_000_000
CHARGE_FULL = 50_000_000


def insert_log_row(
    db_path,
    *,
    time_value,
    event,
    energy_min_wh,
    battery_status=None,
    line_power_name=None,
    line_power_online=None,
):
    connection = connect_database(db_path)
    connection.execute(
        """
        INSERT INTO log (
            time,
            name,
            event,
            cycle_count,
            charge_now,
            current_now,
            voltage_now,
            voltage_min_design,
            energy_now,
            energy_min,
            power_now,
            power_min,
            battery_status,
            line_power_name,
            line_power_online
        ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
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
            battery_status,
            line_power_name,
            line_power_online,
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


def test_report_last_cycle_uses_gain_wording_for_charging_cycle(tmp_path, monkeypatch, capsys):
    db_path = tmp_path / "batterylog.db"

    insert_log_row(db_path, time_value=100, event="suspend", energy_min_wh=49)
    insert_log_row(db_path, time_value=200, event="resume", energy_min_wh=50)

    monkeypatch.setattr("batterylog.core.read_charge_full", lambda battery_name: CHARGE_FULL)

    assert report_last_cycle(db_path) == 0

    output = capsys.readouterr().out
    assert "Gained 1.00 Wh, an average charge rate of 36.00 W" in output
    assert "battery gain" in output


def test_report_history_shows_recent_cycles_and_power_state(tmp_path, capsys):
    db_path = tmp_path / "batterylog.db"

    insert_log_row(
        db_path,
        time_value=100,
        event="suspend",
        energy_min_wh=50,
        battery_status="Discharging",
        line_power_name="AC",
        line_power_online=0,
    )
    insert_log_row(
        db_path,
        time_value=200,
        event="resume",
        energy_min_wh=49,
        battery_status="Discharging",
        line_power_name="AC",
        line_power_online=0,
    )
    insert_log_row(
        db_path,
        time_value=300,
        event="suspend",
        energy_min_wh=48,
        battery_status="Charging",
        line_power_name="AC",
        line_power_online=1,
    )
    insert_log_row(
        db_path,
        time_value=400,
        event="resume",
        energy_min_wh=49,
        battery_status="Full",
        line_power_name="AC",
        line_power_online=1,
    )

    assert report_history(db_path, limit=10, discharging_only=False) == 0

    output = capsys.readouterr().out
    assert "Gained 1.00 Wh" in output
    assert "Used 1.00 Wh" in output
    assert "Charging (AC online) -> Full (AC online)" in output


def test_report_summary_supports_discharging_filter(tmp_path, capsys):
    db_path = tmp_path / "batterylog.db"

    insert_log_row(db_path, time_value=100, event="suspend", energy_min_wh=50)
    insert_log_row(db_path, time_value=200, event="resume", energy_min_wh=49)
    insert_log_row(db_path, time_value=300, event="suspend", energy_min_wh=48)
    insert_log_row(db_path, time_value=400, event="resume", energy_min_wh=49)

    assert report_summary(db_path, limit=10, discharging_only=True) == 0

    output = capsys.readouterr().out
    assert "Summary for 1 discharge cycles" in output
    assert "Charge cycles:" not in output
    assert "Total discharge: 1.00 Wh" in output


def test_log_event_persists_battery_and_line_power_state(tmp_path, monkeypatch):
    db_path = tmp_path / "batterylog.db"
    snapshot = BatterySnapshot(
        name="BAT0",
        cycle_count=100,
        charge_now=1,
        current_now=2,
        voltage_now=3,
        voltage_min_design=4,
        battery_status="Charging",
        line_power_name="AC",
        line_power_online=1,
    )

    monkeypatch.setattr("batterylog.core.read_battery_snapshot", lambda: snapshot)

    assert log_event(db_path, "resume") == 0

    connection = connect_database(db_path)
    try:
        row = connection.execute(
            """
            SELECT battery_status, line_power_name, line_power_online
            FROM log
            ORDER BY time DESC
            LIMIT 1
            """
        ).fetchone()
    finally:
        connection.close()

    assert row["battery_status"] == "Charging"
    assert row["line_power_name"] == "AC"
    assert row["line_power_online"] == 1
