# Implementation Punchlist

Use this as the active execution checklist for packaging, hook management, and migration work. Keep it updated as items complete or are deferred.

## Phase 1: Package And CLI Foundation

- [ ] Add `pyproject.toml` with `hatchling`, project metadata, console script, and `tool.uv` dev dependencies
- [ ] Create a `src/batterylog/` package layout for the new `batterylog` CLI
- [ ] Keep root `batterylog.py` as a thin legacy compatibility shim for upgraded `/opt` installs
- [ ] Make the shim delegate into packaged code instead of duplicating business logic
- [ ] Make the shim force legacy defaults such as sibling DB resolution
- [ ] Keep the current no-argument report behavior
- [ ] Keep `suspend` and `resume` available for hook use
- [ ] Read the version from package metadata rather than duplicating version strings in code
- [ ] Add `--version` to the packaged CLI and preserve it through the legacy shim

## Phase 2: Paths And Runtime State

- [ ] Implement DB path resolution with this precedence: `--db`, `BATTERYLOG_DB`, `/etc/batterylog/config.toml`, legacy shim sibling DB, XDG state default
- [ ] Use `/etc/batterylog/config.toml` for hook-backed system installs
- [ ] Default new system installs to `/var/lib/batterylog/batterylog.db`
- [ ] Default user-only CLI installs to `$XDG_STATE_HOME/batterylog/batterylog.db`
- [ ] Preserve `/opt/batterylog/batterylog.db` for upgraded legacy installs unless the user explicitly migrates
- [ ] Add an explicit DB path override for development and admin workflows
- [ ] Move schema loading so packaged code can find the schema reliably
- [ ] Set hook-backed DB/config permissions so root writes and normal users can read reports without `sudo`

## Phase 3: Hook Management

- [ ] Add `batterylog install-hook`
- [ ] Add `batterylog uninstall-hook`
- [ ] Generate the hook from the resolved `batterylog` executable path plus an explicit DB path
- [ ] Write hook-backed config to `/etc/batterylog/config.toml`
- [ ] Refuse `install-hook` from `uvx` or any other ephemeral executable path
- [ ] Make hook install idempotent for reinstall and upgrade cases
- [ ] Convert `INSTALL.sh` into a legacy wrapper around the maintained install path
- [ ] Keep legacy `/opt` upgrade behavior working

## Phase 4: Migration

- [ ] Add sqlite schema version tracking with `PRAGMA user_version`
- [ ] Make migration `1` the current-schema baseline with no feature-column changes
- [ ] Implement transparent in-place migration for old or unversioned DBs
- [ ] Create `<db path>.bak` before schema migration and leave it in place
- [ ] Refresh the `.bak` file on each migration attempt
- [ ] Add explicit `batterylog migrate-db` support for path migration
- [ ] Keep path migration opt-in and non-destructive
- [ ] Ensure rollback leaves the original DB authoritative if verification fails

## Phase 5: Reporting And Future Features

- [ ] Preserve existing report output behavior during packaging work
- [ ] Add a `history` or `summary` mode
- [ ] Change net-charge sessions to report battery gain instead of negative usage
- [ ] Add AC or charger state logging with additive schema migration

## Phase 6: Validation And Release

- [ ] Add automated tests for path resolution, migration logic, and CLI parsing once logic is isolated
- [ ] Add packaging smoke tests for `pip`, `uv tool install`, `pipx`, and `uvx`
- [ ] Add legacy-install upgrade tests covering `batterylog.py suspend`, `resume`, and no-arg reporting
- [ ] Add migration tests covering automatic schema upgrade, `.bak` retention, and rollback
- [ ] Update `README.md`, `docs/TESTING.md`, and `docs/PUBLISH.md` as implementation lands
