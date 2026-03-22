# batterylog Plan

## Goal

Keep `batterylog` small and Linux-first, while making it suitable for distribution through:

- `pip install batterylog`
- `uv tool install batterylog`
- `pipx install batterylog`
- `uvx batterylog --help` for ephemeral CLI use

Packaging work should preserve the current suspend/resume logging behavior and avoid adding unnecessary framework complexity.

## Current State

- One Python script (`batterylog.py`) plus `schema.sql` and `batterylog.system-sleep`
- Current install flow moves a source checkout into `/opt`
- The database path is coupled to the script directory
- No `pyproject.toml`, package metadata, or authoritative version source
- Validation is currently smoke-test driven rather than automated-test driven

## Phase 1: Packaging Foundation

1. Add `pyproject.toml` using the same basic pattern as `tweetxvault` and `realitycheck`:
   - `hatchling` build backend
   - `[project]` metadata
   - `[project.scripts]` console entry point
   - `[tool.uv]` dev dependencies
2. Convert the repo to a package layout with a stable CLI entry point.
3. Separate installed code from mutable runtime state:
   - the sqlite database must not live inside the package or tool environment
   - choose a default path that works for a root-run systemd hook and a user-run reporting command
   - keep a simple override for local testing and development
4. Package non-code assets correctly:
   - schema file
   - systemd hook template or generated hook content
5. Add a single authoritative version source and use it consistently in release metadata.

## Phase 2: Install Story

1. Replace the destructive `/opt` move with a documented, non-destructive install flow.
2. Support persistent installs via:
   - `pip`
   - `uv tool install`
   - `pipx`
3. Treat `uvx` as an ephemeral execution path:
   - useful for `--help`, inspection, and no-install smoke tests
   - not the primary path for a persistent systemd-hook deployment
4. Provide a clean way to install or generate the `systemd` sleep hook without hardcoding a source checkout path.
5. Update `README.md` with exact install commands for each supported path.

## Phase 3: Testing And Release

1. Keep the current fast smoke checks:
   - `python3 -m py_compile batterylog.py`
   - `sh -n INSTALL.sh`
   - `sh -n batterylog.system-sleep`
   - `sqlite3 :memory: < schema.sql`
2. Add automated tests once pure logic is isolated from hardware and filesystem effects.
3. Add packaging smoke tests before the first PyPI release:
   - build fresh artifacts
   - run `batterylog --help` from the built artifact
   - verify install paths for `pip`, `uv tool install`, and `pipx`
   - verify a no-install `uvx` help/smoke path
4. Keep `docs/PUBLISH.md` aligned with the real release commands and validation matrix.

## Product Backlog

### Reporting

- Change the last-cycle report so net-charge sessions are shown as battery gain instead of negative `Used X Wh`.
- Add a `history` or `summary` mode for recent suspend sessions, with a filter for net-discharge cycles.
- Keep adjacent `suspend -> resume` pairing as the basis for future history and summary output.

### Logging

- Keep current suspend/resume event capture unchanged while packaging work lands.
- Log AC or charger state at both suspend and resume so charging sessions are explicit instead of inferred.

## Exit Criteria For The First PyPI Release

- `batterylog` installs cleanly via `pip`, `uv tool install`, and `pipx`
- built artifacts pass CLI smoke checks
- README install instructions match reality
- `docs/PUBLISH.md` has concrete passing release commands
- the project no longer depends on moving a source checkout into `/opt`
