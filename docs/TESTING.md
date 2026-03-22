# Testing

This repo does not yet have an automated test suite. Keep validation proportional: syntax checks for every change, plus manual hardware checks when behavior changes.

## Fast Checks

Run the commands that match the files you changed:

```sh
python3 -m py_compile batterylog.py
sh -n INSTALL.sh
sh -n batterylog.system-sleep
sqlite3 :memory: < schema.sql
```

## Manual Smoke Checks

### Report Path

On a development checkout:

```sh
python3 batterylog.py
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
3. Confirm the hook executes the installed script, not the development checkout by accident.
4. Confirm the install step does not silently discard user data.
5. Confirm reinstalling or upgrading an existing legacy install behaves predictably.

### Legacy Compatibility Checks

For changes that affect packaging, install paths, or CLI entry points, also confirm:

1. `batterylog.py suspend` still logs correctly for a legacy install.
2. `batterylog.py resume` still logs correctly for a legacy install.
3. `batterylog.py` with no arguments still prints the last-cycle report.
4. An existing `/opt/batterylog/batterylog.db` install is not silently moved or broken during upgrade.

### Packaging Smoke Checks

Once packaging exists, release validation should also confirm:

1. the project builds fresh artifacts successfully
2. the built package can run `batterylog --help`
3. persistent installs work via `pip`, `uv tool install`, and `pipx`
4. an ephemeral `uvx` help or smoke path works for quick verification

## Change-Based Expectations

- Docs-only changes: proofread paths, commands, and cross-references.
- `schema.sql` changes: run the schema check and verify inserts/queries in `batterylog.py` still match.
- `batterylog.py` changes: run `py_compile` plus the relevant manual smoke check.
- Packaging or release changes: run the checks listed in `docs/PUBLISH.md`.

## Reporting

- Record the exact commands you ran in your summary or commit notes.
- If a hardware-dependent test was skipped, say what was skipped and why.
