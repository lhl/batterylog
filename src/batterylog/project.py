from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib


def find_repo_root(start: Path | None = None) -> Path | None:
    current = (start or Path(__file__)).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").exists():
            return candidate

    return None


def load_toml_file(path: Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)
