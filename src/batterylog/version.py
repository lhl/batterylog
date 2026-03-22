from importlib.metadata import PackageNotFoundError, version

from batterylog.project import find_repo_root, load_toml_file


def get_version() -> str:
    try:
        return version("batterylog")
    except PackageNotFoundError:
        return _read_pyproject_version()


def _read_pyproject_version() -> str:
    repo_root = find_repo_root()
    if repo_root is None:
        return "0+unknown"

    pyproject = load_toml_file(repo_root / "pyproject.toml")
    project = pyproject.get("project")
    if not isinstance(project, dict):
        return "0+unknown"

    version_value = project.get("version")
    if not isinstance(version_value, str):
        return "0+unknown"

    return version_value


__version__ = get_version()
