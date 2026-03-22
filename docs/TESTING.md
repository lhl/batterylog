# Testing

This repo now has a small pytest suite for CLI and hook-management logic. Keep validation proportional: syntax checks for every change, pytest for pure logic, plus manual hardware checks when behavior changes.

## Fast Checks

Run the commands that match the files you changed:

```sh
python3 -m py_compile batterylog.py src/batterylog/*.py tests/*.py
sh -n INSTALL.sh
sh -n batterylog.system-sleep
sqlite3 :memory: < schema.sql
pytest
```

## Manual Smoke Checks

### Report Path

On a development checkout:

```sh
python3 batterylog.py
python3 -c "import sys; sys.path.insert(0, 'src'); from batterylog.cli import main; raise SystemExit(main([]))"
```

Expected result on a fresh checkout: the script initializes `batterylog.db` locally and prints the "No power data available" message.

Expected result on a machine with logged data: the script prints the last suspend/resume summary.

### Suspend / Resume Logging

On a Linux machine with `systemd` and `/sys/class/power_supply/BAT*`:

1. Install or wire the hook to a test location.
2. Trigger one suspend/resume cycle.
3. Verify recent rows were written:

```sh
sqlite3 batterylog.db "select time, event from log order by time desc limit 2;"
```

4. Run the report command and check that the duration and energy numbers look plausible.

### Install Flow

If `INSTALL.sh` or the hook path changes:

1. Test on a disposable checkout, VM, or non-critical host.
2. Confirm the install path is the one documented in `README.md`.
3. Confirm the hook executes the installed command path, not the development checkout by accident.
4. Confirm the install step does not silently discard user data.
5. Confirm reinstalling or upgrading an existing legacy install behaves predictably.

### Legacy Compatibility Checks

For changes that affect packaging, install paths, or CLI entry points, also confirm:

1. `batterylog.py suspend` still logs correctly for a legacy install.
2. `batterylog.py resume` still logs correctly for a legacy install.
3. `batterylog.py` with no arguments still prints the last-cycle report.
4. An existing `/opt/batterylog/batterylog.db` install is not silently moved or broken during upgrade.

### Migration Checks

For changes that affect DB paths or schema, also confirm:

1. an existing legacy DB can still be opened in place
2. old or unversioned DBs transparently migrate in place when opened
3. any explicit path-migration command creates a `.bak` backup before mutating state and leaves it behind
4. migrated DBs pass basic sqlite open/query checks
5. row counts remain stable across a path migration
6. rollback instructions are correct if verification fails

### Packaging Smoke Checks

Once packaging exists, release validation should also confirm:

1. the project builds fresh artifacts successfully
2. the built package can run `batterylog --help`
3. persistent installs work via `pip`, `uv tool install`, and `pipx`
4. an ephemeral `uvx` help or smoke path works for quick verification

Note:

- from the repo root, validate source package execution via direct import with `sys.path.insert(0, 'src')`; `python -m batterylog.cli` is shadowed by the legacy `batterylog.py` shim in this tree

## Change-Based Expectations

- Docs-only changes: proofread paths, commands, and cross-references.
- `schema.sql` changes: run the schema check and verify inserts/queries in `batterylog.py` still match.
- `batterylog.py` changes: run `py_compile` plus the relevant manual smoke check.
- `src/batterylog/*.py` changes: run `py_compile`, `pytest`, and the relevant source CLI smoke checks.
- Packaging or release changes: run the checks listed in `docs/PUBLISH.md`.
- DB path or schema changes: run the migration checks from `docs/MIGRATION.md`.

## Reporting

- Record the exact commands you ran in your summary or commit notes.
- If a hardware-dependent test was skipped, say what was skipped and why.
