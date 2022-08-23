# batterylog
Linux laptop battery logging tool

A simple tool that currently reads your sysfs-class-power numbers and records them to a local sqlite3 db.

It was built to track suspend power usage for Framework laptops.

## Reference
* https://www.kernel.org/doc/Documentation/ABI/testing/sysfs-class-power
* https://community.frame.work/t/high-battery-drain-during-suspend/3736
* https://community.frame.work/t/high-battery-drain-during-suspend-windows-edition/4421
