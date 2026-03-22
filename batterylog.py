#!/usr/bin/env python3
import os
import sys

APP_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(APP_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from batterylog.cli import main


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:], legacy_base_dir=APP_DIR))
