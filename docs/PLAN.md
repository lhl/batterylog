# batterylog Plan

## Goal

Keep `batterylog` small and Linux-first, while making it suitable for distribution through:

- `pip install batterylog`
- `uv tool install batterylog`
- `pipx install batterylog`
- `uvx batterylog --help` for ephemeral CLI use

Packaging work should preserve the current suspend/resume logging behavior and avoid adding unnecessary framework complexity.
It should also preserve compatibility for existing `INSTALL.sh` users instead of forcing a flag day migration.

## Release Sequencing

- Treat the pre-doc legacy baseline commit `d15c5d6` as the historical `v0.1` tag point.
- Do not plan a separate `v0.1.1` maintenance release.
- The main near-term target is a legacy-safe `v0.2`, which can include the packaging refactor, compatibility work, and bug fixes that make sense to land together.
- Fold bug fixes into the implementation phases where they make the most sense instead of preserving artificial release boundaries.

## Backward Compatibility Requirements

- Existing legacy behavior is a hard compatibility surface:
  - `batterylog.py suspend`
  - `batterylog.py resume`
  - `batterylog.py` with no arguments for the last-cycle report
- `batterylog.py` is retained for legacy installs only. New packaging and docs should center the packaged `batterylog` command.
- Existing `/opt/batterylog` installs must keep working across upgrades.
- Do not silently move an existing legacy database to a new default path.
- Transparent in-place schema upgrades are allowed when a DB version is old or missing.
- New features should be additive commands or flags, not behavior changes to the existing commands.

## Current State

- A `pyproject.toml` and `src/batterylog/` package skeleton now exist, with `batterylog.py` retained as a legacy shim
- The packaged CLI now supports `install-hook` and `uninstall-hook`, and `INSTALL.sh` delegates legacy hook setup to that managed path
- Legacy installs still default to a DB beside the script, while packaged hook installs now default to `/var/lib/batterylog/batterylog.db`
- Validation now includes a small pytest suite for CLI dispatch and hook-management filesystem behavior
- There is no real schema migration system yet; startup only runs `CREATE TABLE IF NOT EXISTS`

## Phase 1: Packaging Foundation

1. Add `pyproject.toml` using the same basic pattern as `tweetxvault` and `realitycheck`:
   - `hatchling` build backend
   - `[project]` metadata
   - `[project.scripts]` console entry point
   - `[tool.uv]` dev dependencies
   - keep the authoritative version in `pyproject.toml` and read it from package metadata at runtime if needed
   - use a `src/batterylog/` package layout
2. Convert the repo to a package layout with a stable CLI entry point.
   - keep `batterylog.py` as a thin legacy compatibility shim for upgraded `/opt` installs
   - have the shim delegate into the packaged implementation rather than duplicating logic
   - have the shim force legacy defaults such as sibling DB resolution
   - keep no-argument reporting behavior
   - keep `suspend` and `resume` available for hook use
   - add `--version` using package metadata and preserve it through the legacy shim
   - add new admin commands such as hook install/uninstall and DB migration as additive CLI surface
3. Separate installed code from mutable runtime state:
   - the sqlite database must not live inside the package or tool environment
   - use explicit DB path precedence:
     1. `--db`
     2. `BATTERYLOG_DB`
     3. `/etc/batterylog/config.toml` `db_path`
     4. legacy shim default: sibling `batterylog.db`
     5. user default: `$XDG_STATE_HOME/batterylog/batterylog.db`
   - keep a simple override for local testing and development
   - use `/etc/batterylog/config.toml` for hook-backed system installs so CLI reporting and the hook share the same DB path
   - new system installs should default to `/var/lib/batterylog/batterylog.db`
   - user-only CLI mode should default to `$XDG_STATE_HOME/batterylog/batterylog.db`
   - existing legacy installs should keep using `/opt/batterylog/batterylog.db` unless the user explicitly migrates
   - for hook-backed installs, prefer root-owned but world-readable state so normal users can run reports without `sudo`
4. Package non-code assets correctly:
   - schema file
   - systemd hook template or generated hook content
   - package a generated hook path around the current resolved `batterylog` executable plus an explicit DB path
   - write hook-backed system config to `/etc/batterylog/config.toml`
5. Add a single authoritative version source and use it consistently in release metadata.
6. Add a real migration mechanism for sqlite schema changes:
   - track schema version with `PRAGMA user_version`
   - support additive migrations for future columns such as charger state
   - transparently migrate older or unversioned DBs in place
   - treat migration `1` as the current-schema baseline rather than bundling in new feature columns
   - do not rely on `CREATE TABLE IF NOT EXISTS` for upgrades

## Phase 2: Install Story

1. Keep `INSTALL.sh` working for existing users, but make reinstall and upgrade behavior safer and more predictable.
2. Support persistent installs via:
   - `pip`
   - `uv tool install`
   - `pipx`
   - document that hook-backed system installs should prefer a root-owned stable executable path
3. Treat `uvx` as an ephemeral execution path:
   - useful for `--help`, inspection, and no-install smoke tests
   - not the primary path for a persistent systemd-hook deployment
   - `install-hook` should refuse to run from `uvx` or any other ephemeral executable path
4. Fix the legacy installer so it can handle reinstall and upgrade cases without breaking the existing deployment unexpectedly.
5. Provide a clean way to install or generate the `systemd` sleep hook without hardcoding a source checkout path.
6. Update `README.md` with exact install commands for each supported path, clearly marking `INSTALL.sh` as legacy but still supported.
7. Document the migration and rollback workflow in `docs/MIGRATION.md`.

## Phase 3: Testing And Release

1. Keep the current fast smoke checks:
   - `python3 -m py_compile batterylog.py src/batterylog/*.py tests/*.py`
   - `sh -n INSTALL.sh`
   - `sh -n batterylog.system-sleep`
   - `sqlite3 :memory: < schema.sql`
2. Add automated tests once pure logic is isolated from hardware and filesystem effects.
3. Add packaging smoke tests before the first PyPI release:
   - build fresh artifacts
   - run `batterylog --help` from the built artifact
   - verify install paths for `pip`, `uv tool install`, and `pipx`
   - verify a no-install `uvx` help/smoke path
   - verify legacy installs still support `batterylog.py suspend`, `batterylog.py resume`, and zero-argument reporting
   - verify automatic schema upgrade, backup, path-migration, and rollback behavior for legacy databases
4. Keep `docs/PUBLISH.md` aligned with the real release commands and validation matrix.

## Product Backlog

### Reporting

- Change the last-cycle report so net-charge sessions are shown as battery gain instead of negative `Used X Wh`.
- Add a `history` or `summary` mode for recent suspend sessions, with a filter for net-discharge cycles.
- Keep adjacent `suspend -> resume` pairing as the basis for future history and summary output.
- Fold packaging-adjacent bug fixes into the release where they make the most sense rather than preserving artificial boundaries.

### Logging

- Keep current suspend/resume event capture unchanged while packaging work lands.
- Log AC or charger state at both suspend and resume so charging sessions are explicit instead of inferred.

## Migration Strategy

See `docs/MIGRATION.md` for the detailed plan. The short version:

- No automatic legacy DB moves on upgrade.
- Automatic in-place schema upgrades for old or unversioned DBs are expected.
- New packaged system installs use `/var/lib/batterylog/batterylog.db` by default.
- Hook-backed packaged installs share DB configuration via `/etc/batterylog/config.toml`.
- New user-only installs use XDG state by default.
- Legacy `/opt/batterylog/batterylog.db` installs remain supported in place.
- Path moves must be explicit, backed up, and reversible.
- Schema upgrades must be automatic, backed up, and reversible.
- Migrations should leave a `.bak` file in place rather than deleting the backup automatically.
- The backup path should be `<db path>.bak`, refreshed on each migration attempt, and left behind afterward.

## Exit Criteria For The First PyPI Release

- `batterylog` installs cleanly via `pip`, `uv tool install`, and `pipx`
- built artifacts pass CLI smoke checks
- README install instructions match reality
- `docs/PUBLISH.md` has concrete passing release commands
- existing `INSTALL.sh` users have a documented and working upgrade path
- legacy `batterylog.py` command semantics remain unchanged
- migration and rollback behavior is documented and tested
