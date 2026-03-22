from importlib import resources
from pathlib import Path


def load_schema_sql() -> str:
    try:
        return resources.files("batterylog").joinpath("schema.sql").read_text()
    except FileNotFoundError:
        repo_root = Path(__file__).resolve().parents[2]
        return (repo_root / "schema.sql").read_text()
