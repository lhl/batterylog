# batterylog Agent Guide

`batterylog` is a small Linux utility. Keep process light, keep docs honest, and prefer changes that make packaging and distribution easier rather than adding heavyweight project management.

## Project Shape

- `batterylog.py`: main script for logging and last-cycle reporting
- `batterylog.system-sleep`: systemd hook that records `suspend` and `resume`
- `schema.sql`: sqlite schema
- `INSTALL.sh`: current install helper
- `README.md`: user-facing overview
- `docs/README.md`: index of development docs
- `docs/PLAN.md`: active implementation and packaging plan
- `docs/TESTING.md`: validation commands and manual smoke checks
- `docs/PUBLISH.md`: release checklist and packaging gate

## Working Rules

- Run `git status -sb` before editing and before committing.
- For larger changes, align with `docs/PLAN.md` before expanding scope.
- Keep changes small and easy to verify.
- Leave unrelated dirty or untracked files alone.
- Do not edit ad hoc note files like `RESEARCH.md` or `TODO.md` unless the task actually requires it.
- Do not commit local databases, build artifacts, virtualenvs, or host-specific paths.

## Testing Expectations

Run the smallest relevant checks from `docs/TESTING.md`.

Minimum expectations by change type:

- Python changes: `python3 -m py_compile batterylog.py`
- Shell changes: `sh -n INSTALL.sh` and `sh -n batterylog.system-sleep`
- Schema changes: `sqlite3 :memory: < schema.sql`
- Install, suspend/resume, or reporting changes: manual Linux smoke test on a machine with `/sys/class/power_supply/BAT*`

If a required manual or hardware-dependent check cannot be run, say so explicitly.

## Release And Packaging

- Follow `docs/PUBLISH.md` for release preparation.
- Do not claim the project is PyPI-ready unless packaging metadata, versioning, build steps, and install docs all match reality.
- Prefer one authoritative version location once packaging work begins.
- Treat the current `/opt`-based install flow as legacy behavior; do not deepen that coupling unless the task is explicitly about maintaining it.

## Git

- Never use `git add .`, `git add -A`, or `git commit -a`.
- Stage only the files for the current task.
- Review staged changes with `git diff --staged --name-only` and `git diff --staged`.
- Commit completed logical units with conventional prefixes such as `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, or `chore:`.

## Repo-Specific Notes

- This project is Linux- and sysfs-specific. Do not claim broader portability without testing.
- Keep release and install docs synchronized with the actual supported path.
- Prefer straightforward refactors that make later packaging or testing easier, especially splitting pure logic from hardware and filesystem effects.
