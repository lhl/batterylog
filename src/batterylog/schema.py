from importlib import resources
from pathlib import Path

from batterylog.project import find_repo_root


def load_schema_sql() -> str:
    try:
        return resources.files("batterylog").joinpath("schema.sql").read_text()
    except FileNotFoundError:
        repo_root = find_repo_root(Path(__file__))
        if repo_root is None:
            raise

        return (repo_root / "schema.sql").read_text()
