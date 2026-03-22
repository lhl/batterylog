#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
TARGET_DIR=/opt/batterylog

echo "batterylog legacy install: staging files in ${TARGET_DIR}"

if [ "$SCRIPT_DIR" != "$TARGET_DIR" ]; then
    sudo install -d -m 0755 "$TARGET_DIR"
    sudo install -d -m 0755 "$TARGET_DIR/src"

    sudo rm -rf "$TARGET_DIR/src/batterylog" "$TARGET_DIR/docs"

    sudo install -m 0755 "$SCRIPT_DIR/batterylog.py" "$TARGET_DIR/batterylog.py"
    sudo install -m 0755 "$SCRIPT_DIR/batterylog.system-sleep" "$TARGET_DIR/batterylog.system-sleep"
    sudo install -m 0755 "$SCRIPT_DIR/INSTALL.sh" "$TARGET_DIR/INSTALL.sh"
    sudo install -m 0644 "$SCRIPT_DIR/schema.sql" "$TARGET_DIR/schema.sql"
    sudo install -m 0644 "$SCRIPT_DIR/pyproject.toml" "$TARGET_DIR/pyproject.toml"
    sudo install -m 0644 "$SCRIPT_DIR/README.md" "$TARGET_DIR/README.md"
    sudo install -m 0644 "$SCRIPT_DIR/LICENSE" "$TARGET_DIR/LICENSE"
    sudo cp -R "$SCRIPT_DIR/src/batterylog" "$TARGET_DIR/src/batterylog"
    sudo cp -R "$SCRIPT_DIR/docs" "$TARGET_DIR/docs"
else
    echo "Running from ${TARGET_DIR}; refreshing hook/config only."
fi

sudo python3 "$TARGET_DIR/batterylog.py" install-hook \
    --db "$TARGET_DIR/batterylog.db" \
    --hook-command "$TARGET_DIR/batterylog.py"
