#!/bin/sh

echo 'This app requires sqlite3 and python3 to run'

# Create Local database
sqlite3 batterylog.db < schema.sql

# Run logging on suspend and resume
sudo cp batterylog.system-sleep /usr/lib/systemd/system-sleep/batterylog

# Install
sudo mkdir -p /opt
sudo mv ../batterylog /opt/batterylog

