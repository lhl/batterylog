import time
from decimal import Decimal
from pathlib import Path

from batterylog.db import connect_database
from batterylog.power import read_battery_snapshot, read_charge_full


NO_DATA_MESSAGE = (
    "No power data available. If this is your first time running batterylog, "
    "try suspending and resuming first."
)

NO_BATTERY_MESSAGE = "Sorry we couldn't find a battery in /sys/class/power_supply"


def log_event(db_path: Path, event: str) -> int:
    snapshot = read_battery_snapshot()
    if snapshot is None:
        print(NO_BATTERY_MESSAGE)
        return 0

    connection = connect_database(db_path)
    cursor = connection.cursor()
    sql = "INSERT INTO log VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    values = (
        int(time.time()),
        snapshot.name,
        event,
        snapshot.cycle_count,
        snapshot.charge_now,
        snapshot.current_now,
        snapshot.voltage_now,
        snapshot.voltage_min_design,
        snapshot.energy_now,
        snapshot.energy_min,
        snapshot.power_now,
        snapshot.power_min,
    )
    cursor.execute(sql, values)
    connection.commit()
    connection.close()
    return 0


def report_last_cycle(db_path: Path) -> int:
    connection = connect_database(db_path)
    cursor = connection.cursor()

    resume = cursor.execute(
        """
        SELECT * FROM log
        WHERE event = 'resume'
        ORDER BY time DESC
        LIMIT 1
        """
    ).fetchone()

    suspend = cursor.execute(
        """
        SELECT * FROM log
        WHERE event = 'suspend'
        AND time <= ?
        ORDER BY time DESC
        LIMIT 1
        """,
        (resume["time"],),
    ).fetchone() if resume is not None else None

    connection.close()

    if resume is None or suspend is None:
        print(NO_DATA_MESSAGE)
        return 0

    delta_s = resume["time"] - suspend["time"]
    if delta_s <= 0:
        print(NO_DATA_MESSAGE)
        return 0

    delta_h = Decimal(delta_s) / Decimal(3600)
    energy_used_wh = Decimal(suspend["energy_min"] - resume["energy_min"]) / Decimal(1000000000000)
    power_use_w = energy_used_wh / delta_h

    charge_full = read_charge_full(resume["name"])
    energy_full_wh = Decimal(charge_full) / Decimal(1000000000000) * Decimal(resume["voltage_min_design"])
    percent_per_h = 100 * power_use_w / energy_full_wh

    print("Slept for {:.2f} hours".format(delta_h))
    print("Used {:.2f} Wh, an average rate of {:.2f} W".format(energy_used_wh, power_use_w))

    if power_use_w > 0:
        until_empty_h = Decimal(resume["energy_min"]) / Decimal(1000000000000) / power_use_w
        print("At {:.2f} W drain your battery would be empty in {:.2f} hours".format(power_use_w, until_empty_h))

    print(
        "For your {:.2f} Wh battery this is {:.2f}%/hr or {:.2f}%/day".format(
            energy_full_wh,
            percent_per_h,
            percent_per_h * 24,
        )
    )
    return 0
