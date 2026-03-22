import sqlite3

import pytest

import batterylog.migrate as migrate_module
from batterylog.db import connect_database
from batterylog.migrate import (
    CURRENT_SCHEMA_VERSION,
    MigrationError,
    database_backup_path,
    migrate_database_path,
)
from batterylog.schema import load_schema_sql


def create_unversioned_db(db_path):
    connection = sqlite3.connect(str(db_path))
    connection.executescript(load_schema_sql())
    connection.execute(
        "INSERT INTO log VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            100,
            "BAT0",
            "resume",
            100,
            0,
            0,
            0,
            1_000_000,
            1_000_000_000_000,
            1_000_000_000_000,
            0,
            0,
        ),
    )
    connection.commit()
    connection.close()


def read_user_version(db_path):
    connection = sqlite3.connect(str(db_path))
    try:
        return int(connection.execute("PRAGMA user_version").fetchone()[0])
    finally:
        connection.close()


def read_log_count(db_path):
    connection = sqlite3.connect(str(db_path))
    try:
        return int(connection.execute("SELECT COUNT(*) FROM log").fetchone()[0])
    finally:
        connection.close()


def test_connect_database_migrates_unversioned_db_and_keeps_backup(tmp_path):
    db_path = tmp_path / "batterylog.db"
    create_unversioned_db(db_path)

    connection = connect_database(db_path)
    try:
        assert int(connection.execute("PRAGMA user_version").fetchone()[0]) == CURRENT_SCHEMA_VERSION
        assert int(connection.execute("SELECT COUNT(*) FROM log").fetchone()[0]) == 1
    finally:
        connection.close()

    backup_path = database_backup_path(db_path)
    assert backup_path.exists()
    assert read_user_version(backup_path) == 0
    assert read_log_count(backup_path) == 1


def test_connect_database_restores_original_db_on_migration_failure(tmp_path, monkeypatch):
    db_path = tmp_path / "batterylog.db"
    create_unversioned_db(db_path)

    def failing_migration(connection):
        raise sqlite3.OperationalError("simulated migration failure")

    monkeypatch.setitem(migrate_module.MIGRATIONS, 1, failing_migration)

    with pytest.raises(MigrationError, match="Restored from"):
        connect_database(db_path)

    assert read_user_version(db_path) == 0
    assert read_log_count(db_path) == 1
    assert database_backup_path(db_path).exists()


def test_migrate_database_path_copies_db_and_preserves_source_backup(tmp_path):
    source_path = tmp_path / "source.db"
    destination_path = tmp_path / "destination.db"
    create_unversioned_db(source_path)

    assert migrate_database_path(source_path, destination_path) == 0

    assert source_path.exists()
    assert destination_path.exists()
    assert database_backup_path(source_path).exists()

    assert read_user_version(source_path) == CURRENT_SCHEMA_VERSION
    assert read_user_version(destination_path) == CURRENT_SCHEMA_VERSION
    assert read_user_version(database_backup_path(source_path)) == 0
    assert read_log_count(source_path) == 1
    assert read_log_count(destination_path) == 1


def test_migrate_database_path_removes_partial_destination_on_failure(tmp_path, monkeypatch):
    source_path = tmp_path / "source.db"
    destination_path = tmp_path / "destination.db"
    create_unversioned_db(source_path)

    def failing_verify(db_path, *, expected_version):
        raise MigrationError("simulated verification failure")

    monkeypatch.setattr("batterylog.migrate.verify_database_file", failing_verify)

    with pytest.raises(MigrationError, match="simulated verification failure"):
        migrate_database_path(source_path, destination_path)

    assert source_path.exists()
    assert database_backup_path(source_path).exists()
    assert not destination_path.exists()
