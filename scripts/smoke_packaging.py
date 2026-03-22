#!/usr/bin/env python3
import os
import shutil
import subprocess
import tempfile
import venv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    require_command("python3")
    require_command("uv")

    with tempfile.TemporaryDirectory(prefix="batterylog-packaging-") as temp_dir:
        workspace = Path(temp_dir)
        dist_dir = workspace / "dist"
        build_distributions(dist_dir)
        wheel_path = find_single(dist_dir, "*.whl")

        smoke_pip_install(workspace, wheel_path)
        smoke_uv_tool_install(workspace, wheel_path)
        smoke_pipx_install(workspace, wheel_path)
        smoke_uvx_run(workspace, wheel_path)

    print("Packaging smoke checks passed.")
    return 0


def build_distributions(dist_dir: Path) -> None:
    dist_dir.mkdir(parents=True, exist_ok=True)
    if python_module_exists("build"):
        run_command(["python3", "-m", "build", "--outdir", str(dist_dir)], cwd=ROOT)
        return

    run_command(["uv", "build", "--out-dir", str(dist_dir), str(ROOT)], cwd=ROOT)


def smoke_pip_install(workspace: Path, wheel_path: Path) -> None:
    venv_dir = workspace / "pip-venv"
    create_venv(venv_dir)
    python_path = venv_dir / "bin" / "python"
    command_path = venv_dir / "bin" / "batterylog"

    run_command([str(python_path), "-m", "pip", "install", "--force-reinstall", str(wheel_path)])
    run_command([str(command_path), "--version"])
    run_command([str(command_path), "--help"])


def smoke_uv_tool_install(workspace: Path, wheel_path: Path) -> None:
    env = os.environ.copy()
    env["UV_TOOL_DIR"] = str(workspace / "uv-tools")
    env["XDG_BIN_HOME"] = str(workspace / "uv-bin")
    env["UV_CACHE_DIR"] = str(workspace / "uv-cache")
    command_path = Path(env["XDG_BIN_HOME"]) / "batterylog"

    run_command(["uv", "tool", "install", "--force", str(wheel_path)], env=env)
    run_command([str(command_path), "--version"], env=env)
    run_command([str(command_path), "--help"], env=env)


def smoke_pipx_install(workspace: Path, wheel_path: Path) -> None:
    pipx_command = shutil.which("pipx")
    env = os.environ.copy()
    env["PIPX_HOME"] = str(workspace / "pipx-home")
    env["PIPX_BIN_DIR"] = str(workspace / "pipx-bin")
    command_path = Path(env["PIPX_BIN_DIR"]) / "batterylog"

    if pipx_command is None:
        pipx_venv = workspace / "pipx-bootstrap"
        create_venv(pipx_venv)
        python_path = pipx_venv / "bin" / "python"
        pipx_command = str(pipx_venv / "bin" / "pipx")
        run_command([str(python_path), "-m", "pip", "install", "pipx"])

    run_command([str(pipx_command), "install", "--force", str(wheel_path)], env=env)
    run_command([str(command_path), "--version"], env=env)
    run_command([str(command_path), "--help"], env=env)


def smoke_uvx_run(workspace: Path, wheel_path: Path) -> None:
    env = os.environ.copy()
    env["UV_CACHE_DIR"] = str(workspace / "uvx-cache")
    run_command(["uvx", "--isolated", "--from", str(wheel_path), "batterylog", "--version"], env=env)
    run_command(["uvx", "--isolated", "--from", str(wheel_path), "batterylog", "--help"], env=env)


def create_venv(path: Path) -> None:
    venv.EnvBuilder(with_pip=True).create(path)


def python_module_exists(name: str) -> bool:
    result = subprocess.run(
        ["python3", "-c", f"import {name}"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def find_single(directory: Path, pattern: str) -> Path:
    matches = sorted(directory.glob(pattern))
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one match for {pattern} in {directory}, found {len(matches)}")
    return matches[0]


def require_command(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(f"Required command not found on PATH: {name}")


def run_command(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, env=env, check=True)


if __name__ == "__main__":
    raise SystemExit(main())
