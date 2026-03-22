from importlib import resources
from pathlib import Path

from batterylog.project import find_repo_root


LEGACY_SCHEMA_V1_SQL = """\
CREATE TABLE IF NOT EXISTS "log" (
\t"time"\tINTEGER,
\t"name"\tTEXT,
        "event" TEXT,
\t"cycle_count"\tINTEGER,
\t"charge_now"\tINTEGER,
\t"current_now"\tINTEGER,
\t"voltage_now"\tINTEGER,
\t"voltage_min_design"\tINTEGER,
\t"energy_now"\tINTEGER,
\t"energy_min"\tINTEGER,
\t"power_now"\tINTEGER,
\t"power_min"\tINTEGER,
\tPRIMARY KEY("time")
);
"""


def load_schema_sql() -> str:
    try:
        return resources.files("batterylog").joinpath("schema.sql").read_text()
    except FileNotFoundError:
        repo_root = find_repo_root(Path(__file__))
        if repo_root is None:
            raise

        return (repo_root / "schema.sql").read_text()


def load_legacy_schema_sql() -> str:
    return LEGACY_SCHEMA_V1_SQL
