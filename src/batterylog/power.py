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
    battery_status: str | None
    line_power_name: str | None
    line_power_online: int | None

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
    line_power_name, line_power_online = read_line_power_state()

    return BatterySnapshot(
        name=battery_dir.name,
        cycle_count=read_int(battery_dir / "cycle_count"),
        charge_now=read_int(battery_dir / "charge_now"),
        current_now=read_int(battery_dir / "current_now"),
        voltage_now=read_int(battery_dir / "voltage_now"),
        voltage_min_design=read_int(battery_dir / "voltage_min_design"),
        battery_status=read_optional_text(battery_dir / "status"),
        line_power_name=line_power_name,
        line_power_online=line_power_online,
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


def find_first_line_power_dir() -> Path | None:
    power_supply_dir = Path("/sys/class/power_supply")
    for supply_dir in sorted(power_supply_dir.iterdir()):
        if not supply_dir.is_dir() or supply_dir.name.startswith("BAT"):
            continue
        if (supply_dir / "online").exists():
            return supply_dir

    return None


def read_line_power_state() -> tuple[str | None, int | None]:
    line_power_dir = find_first_line_power_dir()
    if line_power_dir is None:
        return None, None

    return line_power_dir.name, read_int(line_power_dir / "online")


def read_int(path: Path) -> int:
    return int(path.read_text().strip())


def read_optional_text(path: Path) -> str | None:
    if not path.exists():
        return None

    return path.read_text().strip()
