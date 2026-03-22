# AUR Update Note

This repo does not control the live `batterylog-git` package on the Arch User Repository. We can prepare an updated `PKGBUILD`, but the current AUR maintainer has to accept and publish the change unless the package is orphaned and adopted by someone else.

## What To Do

Recommended handoff flow:

1. Leave a comment on the live AUR package with:
   - a short summary of why the packaging should be updated
   - a link to the relevant upstream commit(s) or release notes
   - a link to this document
2. Ask the maintainer to update both `PKGBUILD` and `.SRCINFO`.
3. If the maintainer is unresponsive for a meaningful stretch, follow the normal AUR request path rather than trying to treat this repo as the publishing source of truth.

## Why This Needs Maintainer Action

- The ArchWiki AUR submission guidelines say that if a package already exists and is maintained, changes should be submitted in a comment for the maintainer's attention.
- The ArchWiki AUR page says that if there is no response from the maintainer after two weeks, an orphan request can be filed.
- The ArchWiki AUR submission guidelines also note that deletion, merge, and orphan requests go through the AUR "Submit Request" flow and are then accepted or rejected by Package Maintainers.

## Recommended Message

Suggested package comment:

```text
Hi, upstream `batterylog` has changed its internal layout for packaging, but it still preserves the legacy `/opt/batterylog` runtime path used by the current AUR package.

I prepared an updated reference PKGBUILD here:
https://github.com/lhl/batterylog/blob/main/docs/AUR-update.md

Main changes:
- stop shipping a pre-created `batterylog.db`
- keep the legacy `/opt/batterylog` layout
- install the packaged Python source tree expected by the legacy shim
- keep the static system-sleep hook path for compatibility

If you want, I can also provide the matching `.SRCINFO`.
```

## Packaging Rationale

The current reference packaging intentionally stays conservative:

- keep `/opt/batterylog` as the runtime location for compatibility with legacy installs
- keep `batterylog.py` as the installed entry point for the AUR package
- keep the static `batterylog.system-sleep` install path instead of forcing the managed hook flow into pacman packaging
- do not ship a pre-created sqlite database
- ship only the files the legacy shim actually needs

This keeps the AUR package aligned with the existing Arch install style while avoiding the old redundant empty database in the package payload.

## Reference PKGBUILD

Use this as the update candidate for `batterylog-git`:

```bash
# Reference PKGBUILD for the current legacy /opt batterylog layout.
# This is intended as a maintainer aid for `batterylog-git`, not as a second
# release channel inside the repo.

# Maintainer: Stetsed <aur.arch@stetsed.xyz>
pkgname=batterylog-git
pkgver=r0.unknown
pkgrel=1
pkgdesc="Battery logging tool (git version)"
arch=('any')
url="https://github.com/lhl/batterylog"
license=('GPL-3.0')
depends=('python')
makedepends=('git')
source=("git+https://github.com/lhl/batterylog.git")
sha256sums=('SKIP')

pkgver() {
	cd "$srcdir/batterylog"
	printf "r%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short HEAD)"
}

build() {
	cd "$srcdir/batterylog"
}

package() {
	cd "$srcdir/batterylog"

	install -Dm755 batterylog.system-sleep "$pkgdir/usr/lib/systemd/system-sleep/batterylog"
	install -Dm755 batterylog.py "$pkgdir/opt/batterylog/batterylog.py"
	install -Dm644 pyproject.toml "$pkgdir/opt/batterylog/pyproject.toml"
	install -Dm644 schema.sql "$pkgdir/opt/batterylog/schema.sql"
	install -Dm644 README.md "$pkgdir/usr/share/doc/$pkgname/README.md"
	install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"

	install -d "$pkgdir/opt/batterylog/src"
	cp -r src/batterylog "$pkgdir/opt/batterylog/src/batterylog"
}
```

## `.SRCINFO`

The maintainer will also need to regenerate `.SRCINFO` after updating `PKGBUILD`:

```sh
makepkg --printsrcinfo > .SRCINFO
```

## Live Package

- AUR package: <https://aur.archlinux.org/packages/batterylog-git>
- AUR package git URL: `ssh://aur@aur.archlinux.org/batterylog-git.git`
