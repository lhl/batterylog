import argparse
import sys
from pathlib import Path
from typing import Sequence

from batterylog.core import (
    DEFAULT_HISTORY_LIMIT,
    log_event,
    report_history,
    report_last_cycle,
    report_summary,
)
from batterylog.hook import HookInstallError, install_hook, uninstall_hook
from batterylog.migrate import MigrationError, migrate_database_path
from batterylog.paths import resolve_db_path
from batterylog.version import get_version


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="batterylog")
    parser.add_argument(
        "command",
        nargs="?",
        choices=[
            "history",
            "install-hook",
            "migrate-db",
            "report",
            "resume",
            "summary",
            "suspend",
            "uninstall-hook",
        ],
        default="report",
        help="Default behavior is report when no command is provided.",
    )
    parser.add_argument("--db", dest="db_path", help="Override the sqlite database path.")
    parser.add_argument("--from", dest="source_db_path", help="Source database path for migrate-db.")
    parser.add_argument("--to", dest="destination_db_path", help="Destination database path for migrate-db.")
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_HISTORY_LIMIT,
        help="Limit history or summary output to the most recent N complete cycles.",
    )
    parser.add_argument(
        "--discharging-only",
        action="store_true",
        help="Only include net-discharge cycles in history or summary output.",
    )
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
    if args.limit <= 0:
        parser.error("--limit must be a positive integer")

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
        except MigrationError as exc:
            print(exc, file=sys.stderr)
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

    if args.command == "migrate-db":
        if not args.source_db_path or not args.destination_db_path:
            parser.error("migrate-db requires --from and --to")

        try:
            return migrate_database_path(
                Path(args.source_db_path),
                Path(args.destination_db_path),
            )
        except MigrationError as exc:
            print(exc, file=sys.stderr)
            return 1

    db_path = resolve_db_path(args.db_path, legacy_base_dir=legacy_base_dir)

    try:
        if args.command == "history":
            return report_history(
                db_path,
                limit=args.limit,
                discharging_only=args.discharging_only,
            )

        if args.command in {"suspend", "resume"}:
            return log_event(db_path, args.command)

        if args.command == "summary":
            return report_summary(
                db_path,
                limit=args.limit,
                discharging_only=args.discharging_only,
            )

        return report_last_cycle(db_path)
    except MigrationError as exc:
        print(exc, file=sys.stderr)
        return 1


def console_main() -> int:
    return main()
