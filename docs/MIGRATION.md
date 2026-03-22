# Migration

This document covers installation-path migration, database-path migration, and future schema migration for `batterylog`.

## Goals

- keep existing `/opt/batterylog` installs working
- avoid silent data moves or destructive upgrades
- support cleaner defaults for new packaged installs
- provide a safe path for future schema evolution

## Current State

Today, legacy installs behave like this:

- code lives in `/opt/batterylog`
- the sleep hook calls `/opt/batterylog/batterylog.py`
- the database lives at `/opt/batterylog/batterylog.db`
- startup now upgrades old or unversioned DBs in place to `PRAGMA user_version = 1`
- automatic schema migration leaves `<db path>.bak` in place

## Target State

### Legacy Installs

Existing legacy installs remain valid:

- `batterylog.py suspend`
- `batterylog.py resume`
- `batterylog.py` with no arguments
- database stays at `/opt/batterylog/batterylog.db` by default

Legacy upgrades should update code and hook behavior without forcing a database move.

### New Packaged System Installs

For installs that use the packaged CLI and a system sleep hook:

- command entry point: `batterylog`
- default database path: `/var/lib/batterylog/batterylog.db`
- hook installation managed by explicit CLI commands
- prefer a root-owned stable executable path for the installed command
- shared config path: `/etc/batterylog/config.toml`
- DB and config should be root-owned but world-readable so reporting does not require `sudo`
- `install-hook` should refuse to run from `uvx` or any other ephemeral executable path
- minimal config contract: top-level `db_path = "/path/to/batterylog.db"`

### New User-Only CLI Installs

For non-hook, user-local usage:

- command entry point: `batterylog`
- default database path: `$XDG_STATE_HOME/batterylog/batterylog.db`
- fallback when `XDG_STATE_HOME` is unset: `~/.local/state/batterylog/batterylog.db`

## DB Path Resolution Precedence

The runtime should resolve the active DB path in this order:

1. `--db`
2. `BATTERYLOG_DB`
3. `/etc/batterylog/config.toml` `db_path`
4. legacy shim default: sibling `batterylog.db`
5. user default: `$XDG_STATE_HOME/batterylog/batterylog.db`

For hook-backed packaged installs, `install-hook` should write `/etc/batterylog/config.toml` so the packaged CLI and the sleep hook resolve the same DB path.

## Migration Principles

- Never silently move an existing database.
- Transparent in-place schema migration is preferred when the DB version is old or missing.
- Never mutate an existing database in place without leaving a `.bak` backup behind.
- Never make packaging changes depend on an immediate schema change.
- Prefer additive schema changes over rewrites.
- Keep old rows readable after schema upgrades.
- Make path-migration commands explicit and admin-invoked.
- Allow schema migrations to run automatically on normal startup when needed.
- Prefer root-only write with world-readable DB/config permissions for hook-backed installs.

## Planned Migration Surfaces

### 1. Legacy Install Upgrade

This is the highest-priority compatibility path.

Expected behavior:

1. user reruns `INSTALL.sh` or the legacy upgrade path
2. code is upgraded in place
3. existing DB at `/opt/batterylog/batterylog.db` keeps working
4. existing command behavior and hook behavior stay intact

Safety requirements:

- do not delete the old DB
- do not silently move the DB to `/var/lib`
- do not require the user to learn the packaged CLI just to keep their current setup working
- when hook-backed packaged installs are introduced, keep CLI reporting aligned with the configured DB path via `/etc/batterylog/config.toml`

### 2. Explicit Database Location Migration

This is optional and only for users who want to move from a legacy DB path to a new standard path.

CLI shape:

```sh
batterylog migrate-db --from /opt/batterylog/batterylog.db --to /var/lib/batterylog/batterylog.db
```

Recommended behavior:

1. validate source DB exists and is readable
2. validate destination parent directory exists or can be created
3. refresh `<source db>.bak` before any source-side migration work and leave it in place
4. if the source DB is old or unversioned, upgrade it in place before copying it
5. if the destination DB already exists, refresh `<destination db>.bak` before overwriting it
6. copy the verified source DB to the destination instead of moving first
7. verify the copied DB opens and contains the expected schema
8. leave the source DB in place unless the user explicitly asks to retire it
9. print the next manual step for updating hook or config paths

Notes:

- `migrate-db` does not accumulate timestamped backups. Each run refreshes the fixed sibling `.bak` path and replaces any existing backup file there.
- When `migrate-db` starts from an old or unversioned source DB, the source path is live-migrated to the current schema first, with its pre-migration state preserved in `<source db>.bak`.
- If the destination path already exists, its previous contents are preserved in `<destination db>.bak` before the verified copy is written.

### 3. Schema Migration

Future features such as charger-state logging will need schema changes.

Current mechanism:

- use `PRAGMA user_version`
- keep numbered migrations in code
- migrate forward in small additive steps
- support older DBs that only have the original `log` table columns
- treat `user_version = 0` or missing version state as a valid upgrade input
- define migration `1` as the current schema baseline with no table changes beyond setting `user_version = 1`
- reserve later migrations such as charger-state columns for subsequent versions

Expected behavior:

1. open the active DB
2. inspect `PRAGMA user_version`
3. if the version is current, continue normally
4. if the version is old or unset, run forward migrations automatically
5. record the final schema version only after successful migration

Default policy:

- schema migration should be transparent to the user
- the current DB path stays the same during schema migration
- a path migration is still a separate explicit operation

Preferred schema policy:

- add columns rather than rewrite the table when practical
- avoid lossy migrations
- avoid changing meanings of existing columns

## Safety Plan

Any DB migration command or schema migration path should follow this order:

1. Preflight
   - confirm DB path
   - confirm writable destination or backup location
   - confirm enough free space for a copied DB plus backup
2. Backup
   - create `<db path>.bak` before altering anything
   - preserve file ownership and mode where relevant
   - refresh the `.bak` file on each migration attempt
   - leave the `.bak` file in place after success or failure
3. Migration
   - run the copy or schema change
   - prefer copy-plus-verify over destructive move for path changes
   - run schema upgrades in a transaction when practical
4. Verification
   - open the migrated DB with sqlite
   - verify the expected table and columns exist
   - verify row counts for the main log table
5. Rollback
   - if verification fails, keep the original DB authoritative
   - leave the backup in place
   - emit exact rollback instructions

## Rollback Rules

- Original legacy DB remains the source of truth until migration is verified.
- Hook or config updates should happen after DB verification, not before.
- If a migration partially succeeds, prefer reverting the hook/config pointer rather than trying to patch forward blindly.
- Never delete the `.bak` file during the same command that created it.
- If an automatic schema migration fails, abort startup cleanly and leave the pre-migration backup available.

## Release Gate For Migration-Sensitive Changes

Before shipping any release that changes install paths, DB defaults, or schema:

1. test upgrade from a realistic legacy `/opt/batterylog` install
2. test a fresh packaged install
3. test migration into the new default DB path
4. test rollback from a failed migration scenario
5. confirm the README and release notes explain the operator-facing behavior
