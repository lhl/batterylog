import sqlite3
from pathlib import Path

from batterylog.paths import ensure_parent_dir
from batterylog.schema import load_schema_sql


def connect_database(db_path: Path) -> sqlite3.Connection:
    ensure_parent_dir(db_path)
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    initialize_database(connection)
    return connection


def initialize_database(connection: sqlite3.Connection) -> None:
    cursor = connection.cursor()
    cursor.executescript(load_schema_sql())
    connection.commit()
