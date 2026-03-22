# Development Docs

- `docs/PLAN.md`: packaging and implementation plan
- `docs/IMPLEMENTATION.md`: execution punchlist for the current work
- `docs/MIGRATION.md`: install, database, and schema migration plan
- `docs/TESTING.md`: validation commands and manual smoke tests
- `docs/PUBLISH.md`: release checklist for tagged releases and future PyPI publishing
- `docs/RESEARCH.md`: local research notes on suspend efficiency, outliers, and surrounding suspend flows
- `docs/AUR-update.md`: maintainer handoff note and reference PKGBUILD for `batterylog-git`
- `scripts/smoke_packaging.py`: isolated packaging smoke runner for build, `pip`, `uv`, `pipx`, and `uvx`
- `packaging/aur/PKGBUILD`: reference Arch AUR packaging for the legacy `/opt` layout

Keep this directory small. Add docs only when they materially help development, testing, or release work.
