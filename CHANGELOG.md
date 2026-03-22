# Changelog

This changelog tracks user-visible changes and release validation for
`batterylog`.

The format is loosely based on Keep a Changelog and is maintained in reverse
chronological order.

## [0.2.0] - 2026-03-22

### Added

- Packaged `batterylog` CLI with support for `pip`, `uv tool install`, `pipx`,
  and `uvx` smoke usage.
- Managed hook administration via `batterylog install-hook` and
  `batterylog uninstall-hook`.
- Explicit database-path migration via
  `batterylog migrate-db --from ... --to ...`.
- Recent-cycle reporting via `batterylog history` and `batterylog summary`,
  including `--discharging-only`.
- Charger-state logging on suspend and resume, backed by schema version `2`.
- Automated packaging smoke coverage and legacy-shim end-to-end tests.

### Changed

- `batterylog.py` is now a legacy compatibility shim for upgraded `/opt`
  installs, while the packaged `batterylog` command is the primary interface.
- `INSTALL.sh` now stages `/opt/batterylog`, preserves legacy DB behavior, and
  delegates hook installation through the maintained code path.
- Negative net-charge sessions are now reported as battery gain instead of
  negative usage.
- README, migration docs, testing docs, publish docs, and AUR handoff docs were
  expanded for distribution and release work.

### Fixed

- Automatic schema migration now leaves a `.bak` backup in place, restores on
  failure, and keeps connection ownership with the caller.
- `schema.sql` now reflects the current target schema, while migration logic
  keeps a frozen legacy v1 baseline for upgrades.
- Reporting no longer relies on a hardcoded battery path and now pairs complete
  `suspend -> resume` cycles more robustly.
- Hook install/update paths now use atomic writes and rollback behavior.

### Validation

- `python3 -m py_compile batterylog.py src/batterylog/*.py tests/*.py scripts/*.py`
- `pytest`
- `bash -n INSTALL.sh`
- `sh -n batterylog.system-sleep`
- `sqlite3 :memory: < schema.sql`
- `python3 scripts/smoke_packaging.py`
- `uv run --with build --with twine python -m build`
- `uv run --with build --with twine python -m twine check dist/*`

## [0.1.0] - 2023-06-21

### Added

- Initial legacy `/opt/batterylog` release with `batterylog.py suspend`,
  `batterylog.py resume`, and zero-argument last-cycle reporting.
- SQLite logging of suspend/resume battery state from Linux sysfs power data.
- System sleep hook support for automatic suspend/resume event capture.
