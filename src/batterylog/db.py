import sqlite3
from pathlib import Path

from batterylog.migrate import ensure_database_schema
from batterylog.paths import ensure_parent_dir


def connect_database(db_path: Path) -> sqlite3.Connection:
    ensure_parent_dir(db_path)
    db_existed = db_path.exists()
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    initialize_database(connection, db_path, db_existed=db_existed)
    return connection


def initialize_database(connection: sqlite3.Connection, db_path: Path, *, db_existed: bool) -> None:
    ensure_database_schema(connection, db_path, db_existed=db_existed)
