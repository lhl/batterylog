# Publishing

Use this as the release checklist for tagged releases and future PyPI publishing.

## Current State

As of 2026-03-22, this repo is not yet ready for PyPI:

- packaged CLI metadata exists in `pyproject.toml`
- version metadata exists, and packaging smoke validation now exists via `scripts/smoke_packaging.py`
- legacy `INSTALL.sh` now stages `/opt/batterylog` and delegates to the managed hook install path
- hook-management commands exist and legacy upgrade coverage now exists
- sqlite schema migration, `migrate-db`, and schema version `2` charger-state migration now exist
- the remaining work before PyPI is release-level review and publication, not missing packaging scaffolding

Do not publish to PyPI until those gaps are addressed.

## Release Track

- Historical legacy baseline: tag commit `d15c5d6` as `v0.1` if we want a clean pre-doc reference point.
- Do not plan a separate `v0.1.1` maintenance release.
- Main upcoming release target: a legacy-safe `v0.2` for the packaged CLI, hook management, migration behavior, and the related bug fixes that fit naturally into that work.
- Do not create speculative release entries for versions we are not actually shipping.

## Pre-Release Checklist

Before cutting any release:

1. Run `git status -sb` and confirm only intended files are in scope.
2. Run the relevant checks from `docs/TESTING.md`.
3. Run `python3 scripts/smoke_packaging.py`.
4. Re-read `README.md` and confirm install and usage instructions match the code.
5. Confirm release notes clearly state what changed and any system requirements.
6. If packaging files exist, confirm the version is updated in the authoritative location only.
7. If install paths, DB defaults, or schema changed, run the migration checks from `docs/MIGRATION.md`, including automatic upgrade from an old or unversioned DB.
8. If release work touches install layout or packaging behavior, sanity-check the known `batterylog-git` AUR package or refresh `packaging/aur/PKGBUILD`.

## Git Release Steps

When the tree is clean and validation has passed:

```sh
git status -sb
git add <explicit-file-list>
git diff --staged --name-only
git diff --staged
git commit
git tag -a vX.Y.Z -m "vX.Y.Z"
git push origin main
git push origin vX.Y.Z
```

Never use `git add .`, `git add -A`, or `git commit -a` for release work.

## PyPI Release Gate

Do not run a PyPI upload until all of the following exist and are verified:

1. `pyproject.toml` with build-system and project metadata
2. a repeatable build command such as `python3 -m build` or `uv build`
3. a clean install path for end users, preferably via `pipx` or `pip`
4. a documented console entry point or supported invocation path
5. versioned release notes
6. smoke-tested install paths for `pip`, `uv tool install`, and `pipx`
7. a no-install `uvx` or equivalent help/smoke path for quick verification
8. documented migration and rollback behavior for any install-path, DB-path, or schema change
9. verified transparent schema upgrade behavior for old or unversioned DBs
10. automated legacy-shim coverage for `batterylog.py suspend`, `resume`, and no-arg reporting

Recommended commands once packaging is in place:

```sh
python3 -m build
python3 scripts/smoke_packaging.py
python3 -m twine check dist/*
python3 -m twine upload dist/*
```

## After Release

After publishing:

1. Verify the git tag exists locally and on the remote.
2. Verify the release notes or changelog entry is visible wherever users are sent.
3. If PyPI is used, confirm the package installs in a clean environment.
4. If install instructions changed, update `README.md` in the same release.
