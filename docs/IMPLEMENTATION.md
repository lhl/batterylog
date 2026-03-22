# Implementation Punchlist

Use this as the active execution checklist for packaging, hook management, and migration work. Keep it updated as items complete or are deferred.

## Phase 1: Package And CLI Foundation

- [x] Add `pyproject.toml` with `hatchling`, project metadata, console script, and `tool.uv` dev dependencies
- [x] Create a `src/batterylog/` package layout for the new `batterylog` CLI
- [x] Keep root `batterylog.py` as a thin legacy compatibility shim for upgraded `/opt` installs
- [x] Make the shim delegate into packaged code instead of duplicating business logic
- [x] Make the shim force legacy defaults such as sibling DB resolution
- [x] Keep the current no-argument report behavior
- [x] Keep `suspend` and `resume` available for hook use
- [x] Read the version from package metadata rather than duplicating version strings in code
- [x] Add `--version` to the packaged CLI and preserve it through the legacy shim

## Phase 2: Paths And Runtime State

- [x] Implement DB path resolution with this precedence: `--db`, `BATTERYLOG_DB`, `/etc/batterylog/config.toml`, legacy shim sibling DB, XDG state default
- [x] Use `/etc/batterylog/config.toml` for hook-backed system installs
- [x] Default new system installs to `/var/lib/batterylog/batterylog.db`
- [x] Default user-only CLI installs to `$XDG_STATE_HOME/batterylog/batterylog.db`
- [x] Preserve `/opt/batterylog/batterylog.db` for upgraded legacy installs unless the user explicitly migrates
- [x] Add an explicit DB path override for development and admin workflows
- [x] Move schema loading so packaged code can find the schema reliably
- [x] Set hook-backed DB/config permissions so root writes and normal users can read reports without `sudo`

## Phase 3: Hook Management

- [x] Add `batterylog install-hook`
- [x] Add `batterylog uninstall-hook`
- [x] Generate the hook from the resolved `batterylog` executable path plus an explicit DB path
- [x] Write hook-backed config to `/etc/batterylog/config.toml`
- [x] Refuse `install-hook` from `uvx` or any other ephemeral executable path
- [x] Make hook install idempotent for reinstall and upgrade cases
- [x] Convert `INSTALL.sh` into a legacy wrapper around the maintained install path
- [x] Keep legacy `/opt` upgrade behavior working

## Phase 4: Migration

- [x] Add sqlite schema version tracking with `PRAGMA user_version`
- [x] Make migration `1` the current-schema baseline with no feature-column changes
- [x] Implement transparent in-place migration for old or unversioned DBs
- [x] Create `<db path>.bak` before schema migration and leave it in place
- [x] Refresh the `.bak` file on each migration attempt
- [x] Add explicit `batterylog migrate-db` support for path migration
- [x] Keep path migration opt-in and non-destructive
- [x] Ensure rollback leaves the original DB authoritative if verification fails

## Phase 5: Reporting And Future Features

- [ ] Preserve existing report output behavior during packaging work
- [ ] Add a `history` or `summary` mode
- [ ] Change net-charge sessions to report battery gain instead of negative usage
- [ ] Add AC or charger state logging with additive schema migration

## Phase 6: Validation And Release

- [x] Add automated tests for path resolution and migration logic once that code exists
- [ ] Add packaging smoke tests for `pip`, `uv tool install`, `pipx`, and `uvx`
- [ ] Add legacy-install upgrade tests covering `batterylog.py suspend`, `resume`, and no-arg reporting
- [x] Add migration tests covering automatic schema upgrade, `.bak` retention, and rollback
- [ ] Update `README.md`, `docs/TESTING.md`, and `docs/PUBLISH.md` as implementation lands

## Phase 7: Ecosystem Sanity

- [x] Sanity-check the current `batterylog-git` AUR package against the current tree
- [x] Confirm the current AUR package still works through the legacy `/opt/batterylog` path
- [x] Capture the packaging divergence: the current AUR package ships a pre-created unversioned DB and bypasses managed hook/config generation
- [x] Add a cleaned-up reference PKGBUILD under `packaging/aur/PKGBUILD`
- [x] Keep the reference AUR package on the legacy `/opt/batterylog` layout for compatibility
- [x] Avoid shipping a pre-created database in the reference AUR package
