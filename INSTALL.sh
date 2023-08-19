#!/bin/sh

install_dir="/opt/batterylog"
suspend_resume_script_location="/usr/lib/systemd/system-sleep/batterylog.sleep"  # systemd's location for script running on suspend/resume

echo 'This app requires sqlite3 and python3 to run'

# Create Local database
sqlite3 batterylog.db < schema.sql && echo "Successfully created local database."

# Run logging on suspend and resume
sudo cp batterylog.system-sleep "$suspend_resume_script_location" && echo "Added logging on suspend and resume"

# Install
[ ! -d "/opt" ] && sudo mkdir -p /opt && echo "Created directory /opt as it didn't exist."
sudo cp -r ../batterylog "$install_dir" && echo "Successfully install batterylog in $install_dir."
