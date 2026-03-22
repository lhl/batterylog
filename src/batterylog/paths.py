import os
from pathlib import Path
from typing import Mapping

from batterylog.project import load_toml_file

SYSTEM_CONFIG_PATH = Path("/etc/batterylog/config.toml")


def resolve_db_path(
    cli_db: str | None = None,
    *,
    legacy_base_dir: str | Path | None = None,
    env: Mapping[str, str] | None = None,
    system_config_path: Path = SYSTEM_CONFIG_PATH,
) -> Path:
    active_env = os.environ if env is None else env

    if cli_db:
        return Path(cli_db).expanduser()

    env_db = active_env.get("BATTERYLOG_DB")
    if env_db:
        return Path(env_db).expanduser()

    config_db = read_db_path_from_config(system_config_path)
    if config_db is not None:
        return config_db

    if legacy_base_dir is not None:
        return Path(legacy_base_dir).expanduser() / "batterylog.db"

    return default_user_db_path(active_env)


def default_user_db_path(env: Mapping[str, str]) -> Path:
    state_home = env.get("XDG_STATE_HOME")
    if state_home:
        return Path(state_home).expanduser() / "batterylog" / "batterylog.db"

    return Path.home() / ".local" / "state" / "batterylog" / "batterylog.db"


def ensure_parent_dir(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)


def read_db_path_from_config(config_path: Path) -> Path | None:
    if not config_path.exists():
        return None

    value = load_toml_file(config_path).get("db_path")
    if not value:
        return None

    return Path(str(value)).expanduser()
