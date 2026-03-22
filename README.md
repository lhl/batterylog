# batterylog
Linux laptop battery logging tool

A simple Python app with few dependencies that reads your sysfs-class-power numbers and records them to a local sqlite3 db with an "event" tag.

It was built to track suspend power usage for Framework laptops, but it should work on other Linux laptops that expose battery data through `/sys/class/power_supply`.

## Install Status

Native Python packaging is the recommended install path:

- `pipx install batterylog`
- `uv tool install batterylog`
- `pip install batterylog`

`INSTALL.sh` is the legacy install format. It remains supported for existing installs and upgrades.

Existing legacy command behavior is part of the upgrade contract: `batterylog.py suspend`, `batterylog.py resume`, and the zero-argument report should keep working for upgraded legacy installs.
Existing legacy data is also part of that contract: upgrades should not silently relocate or replace `/opt/batterylog/batterylog.db`.
If schema upgrades are needed in the future, they should happen transparently in place for the active database rather than requiring manual intervention.

## Quick Start

Install `batterylog`, then run:

```sh
batterylog
```

For persistent system hook installs from this repo, the legacy helper still works:

```sh
git clone https://github.com/lhl/batterylog.git
cd batterylog
./INSTALL.sh
```

## Usage

The default invocation reports the most recent complete suspend/resume cycle:

```sh
batterylog
```

Recent-cycle views:

```sh
batterylog history --limit 10
batterylog summary --limit 10
batterylog history --discharging-only
```

Administrative commands:

```sh
batterylog --help
batterylog --version
sudo batterylog install-hook
sudo batterylog uninstall-hook
batterylog migrate-db --from /opt/batterylog/batterylog.db --to /var/lib/batterylog/batterylog.db
```

Charging sessions are reported as battery gain instead of negative usage, and suspend/resume rows now record charger-state context for later inspection.

For legacy `/opt` installs, replace `batterylog` with `/opt/batterylog/batterylog.py`.

## Data Storage

`batterylog` stores its data in a local sqlite database.

Default locations:

- Packaged CLI use without a managed system hook:
  `$XDG_STATE_HOME/batterylog/batterylog.db`
- If `XDG_STATE_HOME` is not set:
  `~/.local/state/batterylog/batterylog.db`
- Managed system hook installs from `sudo batterylog install-hook`:
  `/var/lib/batterylog/batterylog.db`
- Legacy `/opt` installs:
  `/opt/batterylog/batterylog.db`

Path resolution precedence:

- `--db /path/to/batterylog.db`
- `BATTERYLOG_DB=/path/to/batterylog.db`
- `/etc/batterylog/config.toml` written by `install-hook`
- legacy sibling path for `/opt/batterylog/batterylog.py`
- user default XDG state path

Custom paths:

- One-off command:
  `batterylog --db /path/to/batterylog.db`
- Per-shell/session override:
  `BATTERYLOG_DB=/path/to/batterylog.db batterylog`
- Managed system hook with a custom DB:
  `sudo batterylog install-hook --db /path/to/batterylog.db`

What is stored:

- one row per `suspend` or `resume` event
- timestamp and battery identifier
- battery cycle count and raw charge/current/voltage snapshot values
- derived energy/power values used for reporting
- battery status and line-power state when available

Automatic schema upgrades run in place on the active database. When a migration
changes an existing DB, `batterylog` leaves a sibling `.bak` file behind.

## Legacy Install

Make sure you meet the requirements, clone the repo, and run `INSTALL.sh`.

The legacy installer stages or refreshes `/opt/batterylog`, then runs the managed hook installer with the legacy DB path so logging continues to write to `/opt/batterylog/batterylog.db`.

Future installer work will keep this path functioning for upgrades and reinstalls, but new packaged releases should eventually be preferred over this legacy flow.

You can run `/opt/batterylog/batterylog.py` without any parameters and it will calculate the power usage from the last suspend/resume cycle:

```
$ /opt/batterylog/batterylog.py
Slept for 8.72 hours
Used 6.10 Wh, an average rate of 0.70 W
For your 53.67 Wh battery this is 1.30%/hr or 31.29%/day
```

This script looks for the first battery at `/sys/class/power_supply/BAT*`. It has currently only been tested with a Framework laptop, and some machines may not expose every value it expects. The tool is intentionally small and CLI-first: it stores the raw suspend/resume history in sqlite and exposes a few practical reporting commands on top.

The new `history` and `summary` commands cover the most common review use cases without adding a heavier UI layer.

## Native Python Installs

Common install commands:

```sh
pipx install batterylog
uv tool install batterylog
pip install batterylog
```

Ephemeral CLI checks:

```sh
uvx batterylog --help
```

For a persistent system suspend hook from a repo checkout, `INSTALL.sh` is still the simplest documented setup in this project today.

## Requirements

- Linux with battery data exposed through `/sys/class/power_supply`
- systemd
- Python `3.10+`
- `sqlite3` CLI is optional, but useful for manual inspection/debugging

## Packaging

- Arch Linux AUR: [batterylog-git](https://aur.archlinux.org/packages/batterylog-git) packaged by [Stetsed](https://github.com/Stetsed)
- Reference AUR packaging for the current tree: `packaging/aur/PKGBUILD`

## Other Related Tools

- [powertop](https://github.com/fenrus75/powertop) - power usage realtime monitoring swiss army knife; can export reports
- [powerstat](https://github.com/ColinIanKing/powerstat) - useful for measuring idle power usage; generates vmstat-style output and TUI histograms
- [turbostat](https://www.linux.org/docs/man8/turbostat.html) - state/temp/clock/power info for Intel CPUs
- [battery-stats](https://github.com/petterreinholdtsen/battery-stats) - long-term battery logging/capture
- [batstat](https://github.com/petterreinholdtsen/battery-stats) - small C app that does continuous logging of battery info into a sqlite DB
- [uPower](https://upower.freedesktop.org/) - D-Bus layer that stores power history/stats
- [GNOME Power Statistics](https://www.linux.org/docs/man8/turbostat.html) - GUI that [uses uPower stats](https://askubuntu.com/questions/139202/how-can-i-reset-the-battery-statistics-for-the-powermanager)
- [powir](https://github.com/SlapBot/powir) - Windows app, but lots of nice features
- [SleepStudy](https://docs.microsoft.com/en-us/windows-hardware/design/device-experiences/modern-standby-sleepstudy) - Windows built-in that also [generates reports](https://blogs.windows.com/windowsexperience/2014/06/26/sleep-study-diagnose-whats-draining-your-battery-while-the-system-sleeps/)

## Other Related Python Libraries

- [batinfo](https://github.com/nicolargo/batinfo)
- [upower-python](https://github.com/wogscpar/upower-python)

## Reference

- https://www.kernel.org/doc/Documentation/ABI/testing/sysfs-class-power
- https://community.frame.work/t/high-battery-drain-during-suspend/3736
- https://community.frame.work/t/high-battery-drain-during-suspend-windows-edition/4421
