from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import re


def get_version() -> str:
    try:
        return version("batterylog")
    except PackageNotFoundError:
        return _read_pyproject_version()


def _read_pyproject_version() -> str:
    pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
    if not pyproject_path.exists():
        return "0+unknown"

    match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject_path.read_text(), re.MULTILINE)
    if not match:
        return "0+unknown"

    return match.group(1)


__version__ = get_version()
