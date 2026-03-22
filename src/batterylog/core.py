import time
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from sqlite3 import Row

from batterylog.db import connect_database
from batterylog.power import read_battery_snapshot, read_charge_full


NO_DATA_MESSAGE = (
    "No power data available. If this is your first time running batterylog, "
    "try suspending and resuming first."
)

NO_BATTERY_MESSAGE = "Sorry we couldn't find a battery in /sys/class/power_supply"
NO_CAPACITY_MESSAGE = "Battery full-capacity metadata unavailable; skipping percentage estimate."
DEFAULT_HISTORY_LIMIT = 10
SECONDS_PER_HOUR = Decimal(3600)
WH_SCALE = Decimal(1_000_000_000_000)


@dataclass(frozen=True)
class CycleRecord:
    suspend: Row
    resume: Row
    duration_s: int
    energy_delta_wh: Decimal

    @classmethod
    def from_rows(cls, suspend: Row, resume: Row) -> "CycleRecord | None":
        duration_s = int(resume["time"]) - int(suspend["time"])
        if duration_s <= 0:
            return None

        energy_delta_wh = Decimal(int(suspend["energy_min"]) - int(resume["energy_min"])) / WH_SCALE
        return cls(
            suspend=suspend,
            resume=resume,
            duration_s=duration_s,
            energy_delta_wh=energy_delta_wh,
        )

    @property
    def duration_h(self) -> Decimal:
        return Decimal(self.duration_s) / SECONDS_PER_HOUR

    @property
    def energy_abs_wh(self) -> Decimal:
        return abs(self.energy_delta_wh)

    @property
    def average_power_w(self) -> Decimal:
        return self.energy_abs_wh / self.duration_h

    @property
    def is_gain(self) -> bool:
        return self.energy_delta_wh < 0

    @property
    def is_discharge(self) -> bool:
        return self.energy_delta_wh > 0


def log_event(db_path: Path, event: str) -> int:
    snapshot = read_battery_snapshot()
    if snapshot is None:
        print(NO_BATTERY_MESSAGE)
        return 0

    connection = connect_database(db_path)
    cursor = connection.cursor()
    sql = """
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
    """
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
        snapshot.battery_status,
        snapshot.line_power_name,
        snapshot.line_power_online,
    )
    cursor.execute(sql, values)
    connection.commit()
    connection.close()
    return 0


def report_last_cycle(db_path: Path) -> int:
    cycles = load_complete_cycles(db_path)
    if not cycles:
        print(NO_DATA_MESSAGE)
        return 0

    cycle = cycles[-1]
    print("Slept for {:.2f} hours".format(cycle.duration_h))

    if cycle.is_gain:
        print(
            "Gained {:.2f} Wh, an average charge rate of {:.2f} W".format(
                cycle.energy_abs_wh,
                cycle.average_power_w,
            )
        )
    else:
        print(
            "Used {:.2f} Wh, an average rate of {:.2f} W".format(
                cycle.energy_abs_wh,
                cycle.average_power_w,
            )
        )

    charge_full = read_charge_full(cycle.resume["name"])
    energy_full_wh = Decimal(charge_full) / WH_SCALE * Decimal(cycle.resume["voltage_min_design"])
    if energy_full_wh <= 0:
        print(NO_CAPACITY_MESSAGE)
        return 0

    if cycle.is_gain:
        remaining_wh = energy_full_wh - Decimal(cycle.resume["energy_min"]) / WH_SCALE
        if cycle.average_power_w > 0 and remaining_wh > 0:
            until_full_h = remaining_wh / cycle.average_power_w
            print(
                "At {:.2f} W charge your battery would be full in {:.2f} hours".format(
                    cycle.average_power_w,
                    until_full_h,
                )
            )
    elif cycle.average_power_w > 0:
        until_empty_h = Decimal(cycle.resume["energy_min"]) / WH_SCALE / cycle.average_power_w
        print(
            "At {:.2f} W drain your battery would be empty in {:.2f} hours".format(
                cycle.average_power_w,
                until_empty_h,
            )
        )

    percent_per_h = 100 * cycle.average_power_w / energy_full_wh
    if cycle.is_gain:
        print(
            "For your {:.2f} Wh battery this is {:.2f}%/hr or {:.2f}%/day of battery gain".format(
                energy_full_wh,
                percent_per_h,
                percent_per_h * 24,
            )
        )
    else:
        print(
            "For your {:.2f} Wh battery this is {:.2f}%/hr or {:.2f}%/day".format(
                energy_full_wh,
                percent_per_h,
                percent_per_h * 24,
            )
        )
    return 0


def report_history(db_path: Path, *, limit: int = DEFAULT_HISTORY_LIMIT, discharging_only: bool = False) -> int:
    cycles = select_cycles(
        db_path,
        limit=limit,
        discharging_only=discharging_only,
    )
    if not cycles:
        print(NO_DATA_MESSAGE)
        return 0

    for cycle in reversed(cycles):
        print(format_cycle_history_line(cycle))
    return 0


def report_summary(db_path: Path, *, limit: int = DEFAULT_HISTORY_LIMIT, discharging_only: bool = False) -> int:
    cycles = select_cycles(
        db_path,
        limit=limit,
        discharging_only=discharging_only,
    )
    if not cycles:
        print(NO_DATA_MESSAGE)
        return 0

    print(summary_heading(cycles, discharging_only=discharging_only))
    print("Average sleep duration: {:.2f} hours".format(mean_decimal([cycle.duration_h for cycle in cycles])))

    discharge_cycles = [cycle for cycle in cycles if cycle.is_discharge]
    print("Discharge cycles: {}".format(len(discharge_cycles)))
    if discharge_cycles:
        print("Total discharge: {:.2f} Wh".format(sum_decimal([cycle.energy_abs_wh for cycle in discharge_cycles])))
        print(
            "Average discharge rate: {:.2f} W".format(
                mean_decimal([cycle.average_power_w for cycle in discharge_cycles])
            )
        )

    if not discharging_only:
        gain_cycles = [cycle for cycle in cycles if cycle.is_gain]
        neutral_cycles = [cycle for cycle in cycles if not cycle.is_discharge and not cycle.is_gain]
        print("Charge cycles: {}".format(len(gain_cycles)))
        if gain_cycles:
            print("Total gain: {:.2f} Wh".format(sum_decimal([cycle.energy_abs_wh for cycle in gain_cycles])))
            print(
                "Average charge rate: {:.2f} W".format(
                    mean_decimal([cycle.average_power_w for cycle in gain_cycles])
                )
            )
        if neutral_cycles:
            print("Neutral cycles: {}".format(len(neutral_cycles)))

    return 0


def load_complete_cycles(db_path: Path) -> list[CycleRecord]:
    connection = connect_database(db_path)
    try:
        rows = connection.execute(
            """
            SELECT * FROM log
            ORDER BY time ASC
            """
        ).fetchall()
    finally:
        connection.close()

    return build_complete_cycles(rows)


def build_complete_cycles(rows: list[Row]) -> list[CycleRecord]:
    cycles: list[CycleRecord] = []
    pending_suspend: Row | None = None

    for row in rows:
        if row["event"] == "suspend":
            pending_suspend = row
            continue

        if row["event"] != "resume" or pending_suspend is None:
            continue

        cycle = CycleRecord.from_rows(pending_suspend, row)
        pending_suspend = None
        if cycle is not None:
            cycles.append(cycle)

    return cycles


def select_cycles(db_path: Path, *, limit: int, discharging_only: bool) -> list[CycleRecord]:
    cycles = load_complete_cycles(db_path)
    if discharging_only:
        cycles = [cycle for cycle in cycles if cycle.is_discharge]
    if limit <= 0:
        return cycles
    return cycles[-limit:]


def format_cycle_history_line(cycle: CycleRecord) -> str:
    start = datetime.fromtimestamp(cycle.suspend["time"]).strftime("%Y-%m-%d %H:%M")
    end = datetime.fromtimestamp(cycle.resume["time"]).strftime("%Y-%m-%d %H:%M")
    action = "Gained" if cycle.is_gain else "Used"
    average_label = "avg charge" if cycle.is_gain else "avg"
    line = (
        f"{start} -> {end} | {cycle.duration_h:.2f} h | "
        f"{action} {cycle.energy_abs_wh:.2f} Wh | {cycle.average_power_w:.2f} W {average_label}"
    )

    power_state = format_cycle_power_state(cycle)
    if power_state is not None:
        line = f"{line} | {power_state}"

    return line


def format_cycle_power_state(cycle: CycleRecord) -> str | None:
    suspend_state = format_power_state(cycle.suspend)
    resume_state = format_power_state(cycle.resume)
    if suspend_state is None and resume_state is None:
        return None

    return f"{suspend_state or 'unknown'} -> {resume_state or 'unknown'}"


def format_power_state(row: Row) -> str | None:
    battery_status = row["battery_status"]
    line_power_online = row["line_power_online"]
    line_power_name = row["line_power_name"] or "charger"

    if line_power_online is None:
        return battery_status

    charger_state = f"{line_power_name} {'online' if int(line_power_online) else 'offline'}"
    if battery_status:
        return f"{battery_status} ({charger_state})"

    return charger_state


def mean_decimal(values: list[Decimal]) -> Decimal:
    return sum_decimal(values) / Decimal(len(values))


def sum_decimal(values: list[Decimal]) -> Decimal:
    total = Decimal(0)
    for value in values:
        total += value
    return total


def summary_heading(cycles: list[CycleRecord], *, discharging_only: bool) -> str:
    if discharging_only:
        return f"Summary for {len(cycles)} discharge cycles"
    return f"Summary for {len(cycles)} complete cycles"
