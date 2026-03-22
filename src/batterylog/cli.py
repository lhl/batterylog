import argparse
import sys
from pathlib import Path
from typing import Sequence

from batterylog.core import log_event, report_last_cycle
from batterylog.hook import HookInstallError, install_hook, uninstall_hook
from batterylog.paths import resolve_db_path
from batterylog.version import get_version


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="batterylog")
    parser.add_argument(
        "command",
        nargs="?",
        choices=["install-hook", "report", "resume", "suspend", "uninstall-hook"],
        default="report",
        help="Default behavior is report when no command is provided.",
    )
    parser.add_argument("--db", dest="db_path", help="Override the sqlite database path.")
    parser.add_argument("--hook-command", help=argparse.SUPPRESS)
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {get_version()}",
    )
    return parser


def main(argv: Sequence[str] | None = None, *, legacy_base_dir: str | Path | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "install-hook":
        try:
            install_db_path = Path(args.db_path).expanduser() if args.db_path else None
            return install_hook(install_db_path, hook_command=args.hook_command)
        except PermissionError as exc:
            print(
                f"Permission denied while updating managed system paths: {exc}. "
                "Run install-hook as root.",
                file=sys.stderr,
            )
            return 1
        except HookInstallError as exc:
            print(exc, file=sys.stderr)
            return 1

    if args.command == "uninstall-hook":
        try:
            return uninstall_hook()
        except PermissionError as exc:
            print(
                f"Permission denied while updating managed system paths: {exc}. "
                "Run uninstall-hook as root.",
                file=sys.stderr,
            )
            return 1

    db_path = resolve_db_path(args.db_path, legacy_base_dir=legacy_base_dir)

    if args.command in {"suspend", "resume"}:
        return log_event(db_path, args.command)

    return report_last_cycle(db_path)


def console_main() -> int:
    return main()
