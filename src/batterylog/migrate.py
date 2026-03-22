import os
import shutil
import sqlite3
import tempfile
from pathlib import Path

from batterylog.paths import ensure_parent_dir
from batterylog.schema import load_schema_sql


CURRENT_SCHEMA_VERSION = 1


class MigrationError(RuntimeError):
    pass


def ensure_database_schema(connection: sqlite3.Connection, db_path: Path, *, db_existed: bool) -> None:
    current_version = get_user_version(connection)
    if current_version > CURRENT_SCHEMA_VERSION:
        raise MigrationError(
            f"Database at {db_path} uses schema version {current_version}, "
            f"which is newer than this release supports ({CURRENT_SCHEMA_VERSION})."
        )

    if current_version == CURRENT_SCHEMA_VERSION:
        verify_database(connection, expected_version=CURRENT_SCHEMA_VERSION)
        return

    backup_path = None
    if db_existed:
        backup_path = refresh_database_backup(db_path, connection=connection)

    try:
        run_migrations(connection, current_version)
        verify_database(connection, expected_version=CURRENT_SCHEMA_VERSION)
    except Exception as exc:
        safe_rollback(connection)

        if backup_path is None:
            raise MigrationError(f"Failed to initialize database at {db_path}: {exc}") from exc

        try:
            restore_connection_from_backup(connection, db_path)
        except (OSError, sqlite3.Error) as restore_exc:
            raise MigrationError(
                f"Failed to migrate {db_path}: {exc}. Restore from {backup_path} also failed: {restore_exc}"
            ) from exc

        raise MigrationError(f"Failed to migrate {db_path}: {exc}. Restored from {backup_path}.") from exc


def migrate_database_path(source_path: Path, destination_path: Path) -> int:
    source = source_path.expanduser()
    destination = destination_path.expanduser()
    validate_migration_paths(source, destination)

    connection = sqlite3.connect(str(source))
    try:
        starting_version = get_user_version(connection)
        ensure_database_schema(connection, source, db_existed=True)
        connection.close()
        connection = None
    finally:
        if connection is not None:
            connection.close()

    if starting_version == CURRENT_SCHEMA_VERSION:
        source_backup_path = refresh_database_backup(source)
    else:
        source_backup_path = database_backup_path(source)

    destination_backup_path = refresh_destination_backup(destination)

    try:
        copy_file_atomically(source, destination)
        verify_database_file(destination, expected_version=CURRENT_SCHEMA_VERSION)
    except Exception as exc:
        rollback_error = rollback_destination(destination, destination_backup_path)
        if rollback_error is not None:
            raise MigrationError(
                f"Failed to migrate database from {source} to {destination}: {exc}. "
                f"Destination rollback also failed: {rollback_error}"
            ) from exc
        raise MigrationError(f"Failed to migrate database from {source} to {destination}: {exc}") from exc

    print(f"Copied database to {destination}")
    print(f"Refreshed backup at {source_backup_path}")
    if destination_backup_path is not None:
        print(f"Refreshed destination backup at {destination_backup_path}")
    return 0


def validate_migration_paths(source: Path, destination: Path) -> None:
    if not source.exists():
        raise MigrationError(f"Source database does not exist: {source}")

    if not source.is_file():
        raise MigrationError(f"Source database is not a file: {source}")

    if source.resolve(strict=False) == destination.resolve(strict=False):
        raise MigrationError("Source and destination database paths must differ.")

    ensure_parent_dir(destination)


def run_migrations(connection: sqlite3.Connection, current_version: int) -> None:
    for target_version in range(current_version + 1, CURRENT_SCHEMA_VERSION + 1):
        migration = MIGRATIONS.get(target_version)
        if migration is None:
            raise MigrationError(f"No migration is defined for schema version {target_version}.")

        migration(connection)
        set_user_version(connection, target_version)
        connection.commit()


def migrate_to_v1(connection: sqlite3.Connection) -> None:
    connection.executescript(load_schema_sql())


MIGRATIONS = {
    1: migrate_to_v1,
}


def verify_database(connection: sqlite3.Connection, *, expected_version: int) -> None:
    current_version = get_user_version(connection)
    if current_version != expected_version:
        raise MigrationError(
            f"Expected schema version {expected_version}, found {current_version}."
        )

    row = connection.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type = 'table' AND name = 'log'
        """
    ).fetchone()
    if row is None:
        raise MigrationError("Database is missing the log table.")


def verify_database_file(db_path: Path, *, expected_version: int) -> None:
    connection = sqlite3.connect(str(db_path))
    try:
        verify_database(connection, expected_version=expected_version)
    finally:
        connection.close()


def get_user_version(connection: sqlite3.Connection) -> int:
    return int(connection.execute("PRAGMA user_version").fetchone()[0])


def set_user_version(connection: sqlite3.Connection, version: int) -> None:
    connection.execute(f"PRAGMA user_version = {int(version)}")


def database_backup_path(db_path: Path) -> Path:
    return Path(f"{db_path}.bak")


def refresh_database_backup(db_path: Path, *, connection: sqlite3.Connection | None = None) -> Path:
    backup_path = database_backup_path(db_path)

    if connection is None:
        copy_file_atomically(db_path, backup_path)
        return backup_path

    copy_connection_to_path(connection, db_path, backup_path)
    return backup_path


def refresh_destination_backup(destination_path: Path) -> Path | None:
    if not destination_path.exists():
        return None

    backup_path = database_backup_path(destination_path)
    copy_file_atomically(destination_path, backup_path)
    return backup_path


def restore_connection_from_backup(connection: sqlite3.Connection, db_path: Path) -> None:
    backup_path = database_backup_path(db_path)
    source_connection = sqlite3.connect(str(backup_path))
    try:
        source_connection.backup(connection)
    finally:
        source_connection.close()


def rollback_destination(destination_path: Path, destination_backup_path: Path | None) -> OSError | None:
    try:
        if destination_backup_path is None:
            destination_path.unlink(missing_ok=True)
            return None

        copy_file_atomically(destination_backup_path, destination_path)
        return None
    except OSError as exc:
        return exc


def copy_connection_to_path(
    source_connection: sqlite3.Connection,
    metadata_path: Path,
    destination_path: Path,
) -> None:
    ensure_parent_dir(destination_path)
    temp_path = temporary_path(destination_path)
    try:
        destination_connection = sqlite3.connect(str(temp_path))
        try:
            source_connection.backup(destination_connection)
        finally:
            destination_connection.close()

        finalize_temp_copy(temp_path, metadata_path, destination_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def copy_file_atomically(source_path: Path, destination_path: Path) -> None:
    ensure_parent_dir(destination_path)
    temp_path = temporary_path(destination_path)
    try:
        shutil.copy2(source_path, temp_path)
        copy_owner(source_path, temp_path)
        temp_path.replace(destination_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def temporary_path(destination_path: Path) -> Path:
    file_descriptor, temp_name = tempfile.mkstemp(
        dir=destination_path.parent,
        prefix=f".{destination_path.name}.",
    )
    os.close(file_descriptor)
    return Path(temp_name)


def finalize_temp_copy(temp_path: Path, metadata_path: Path, destination_path: Path) -> None:
    try:
        shutil.copystat(metadata_path, temp_path)
        copy_owner(metadata_path, temp_path)
        temp_path.replace(destination_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def copy_owner(source_path: Path, destination_path: Path) -> None:
    if not hasattr(os, "chown"):
        return

    source_stat = source_path.stat()
    try:
        os.chown(destination_path, source_stat.st_uid, source_stat.st_gid)
    except PermissionError:
        pass


def safe_rollback(connection: sqlite3.Connection) -> None:
    try:
        connection.rollback()
    except sqlite3.Error:
        pass
