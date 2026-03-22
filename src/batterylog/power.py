from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BatterySnapshot:
    name: str
    cycle_count: int
    charge_now: int
    current_now: int
    voltage_now: int
    voltage_min_design: int

    @property
    def energy_now(self) -> int:
        return self.charge_now * self.voltage_now

    @property
    def energy_min(self) -> int:
        return self.charge_now * self.voltage_min_design

    @property
    def power_now(self) -> int:
        return self.current_now * self.voltage_now

    @property
    def power_min(self) -> int:
        return self.current_now * self.voltage_min_design


def read_battery_snapshot() -> BatterySnapshot | None:
    battery_dir = find_first_battery_dir()
    if battery_dir is None:
        return None

    return BatterySnapshot(
        name=battery_dir.name,
        cycle_count=read_int(battery_dir / "cycle_count"),
        charge_now=read_int(battery_dir / "charge_now"),
        current_now=read_int(battery_dir / "current_now"),
        voltage_now=read_int(battery_dir / "voltage_now"),
        voltage_min_design=read_int(battery_dir / "voltage_min_design"),
    )


def read_charge_full(battery_name: str | None) -> int:
    if battery_name:
        battery_dir = Path("/sys/class/power_supply") / battery_name
        if battery_dir.exists():
            return read_int(battery_dir / "charge_full")

    battery_dir = find_first_battery_dir()
    if battery_dir is None:
        raise FileNotFoundError("No battery found in /sys/class/power_supply")

    return read_int(battery_dir / "charge_full")


def find_first_battery_dir() -> Path | None:
    power_supply_dir = Path("/sys/class/power_supply")
    batteries = sorted(power_supply_dir.glob("BAT*"))
    return batteries[0] if batteries else None


def read_int(path: Path) -> int:
    return int(path.read_text().strip())
