# batterylog
Linux laptop battery logging tool

A simple Python app with few dependencies that reads your sysfs-class-power numbers and records them to a local sqlite3 db with an "event" tag.

It was built to track suspend power usage for Framework laptops, but is flexible/easily extensible to do all kinds of other stuff.

# Requirements
* sysfs-class-power (`/sys/class/power_supply`)
* systemd
* python3
* sqlite3

## Other Related Tools
* [powertop](https://github.com/fenrus75/powertop) - power usage realtime monitoring swiss army knife; can export reports
* [powerstat](https://github.com/ColinIanKing/powerstat) - most useful tool for measuring idle power usage; generates vmstat-style output and TUI histograms
* [turbostat](https://www.linux.org/docs/man8/turbostat.html) - state/temp/clock/power info for Intel CPUs
* [battery-stats](https://github.com/petterreinholdtsen/battery-stats) - this didn't work for me, but in theory does long-term battery logging/capture
* [batstat](https://github.com/petterreinholdtsen/battery-stats) - small C app that does continuous logging of battery info into a sqlite DB
* [uPower](https://upower.freedesktop.org/) - D-Bus layer that stores power history/stats
* [GNOME Power Statistics](https://www.linux.org/docs/man8/turbostat.html) - GUI that [uses uPower stats](https://askubuntu.com/questions/139202/how-can-i-reset-the-battery-statistics-for-the-powermanager)
* [powir](https://github.com/SlapBot/powir) - Windows app, but lots of nice features, worth mentioning
* [SleepStudy](https://docs.microsoft.com/en-us/windows-hardware/design/device-experiences/modern-standby-sleepstudy) - Windows built-in that also [generates cool reports](https://blogs.windows.com/windowsexperience/2014/06/26/sleep-study-diagnose-whats-draining-your-battery-while-the-system-sleeps/)

## Other Related Python Libraries
* [batinfo](https://github.com/nicolargo/batinfo)
* [upower-python](https://github.com/wogscpar/upower-python)

## Reference
* https://www.kernel.org/doc/Documentation/ABI/testing/sysfs-class-power
* https://community.frame.work/t/high-battery-drain-during-suspend/3736
* https://community.frame.work/t/high-battery-drain-during-suspend-windows-edition/4421
