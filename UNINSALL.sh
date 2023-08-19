#!/bin/sh

installed_dir="/opt/batterylog"
suspend_resume_script_location="/usr/lib/systemd/system-sleep/batterylog.sleep"  # systemd's location for script running on suspend/resume

# if the directory doesn't exist then notify and exit
if [ ! -d "$installed_dir"  ]; then
    echo "Directory $installed_dir not found."
    echo "Since, the directory $installed_dir doesn't exist, assuming the program isn't installed."
    exit 0
fi

# else continuing with removal

# Remove Local database
sudo rm "$installed_dir/batterylog.db" && echo "Removed local database $installed_dir/batterylog.db"

# Remove logging on suspend and resume
sudo rm $suspend_resume_script_location && echo "Removed script present in $suspend_resume_script_location"

# Remove the whole dir
sudo rm -r $installed_dir && echo "Successfully removed the $installed_dir directory"

