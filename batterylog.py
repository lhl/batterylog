#!/usr/bin/python

from   decimal import Decimal
import os
import sqlite3
import sys
import time

# Paths
APP_DIR = os.path.dirname(__file__)
SCHEMA_FILE = APP_DIR + '/schema.sql'
DB_FILE = APP_DIR + '/batterylog.db'

# Connect to DB
con = sqlite3.connect(DB_FILE)
con.row_factory = sqlite3.Row
cur = con.cursor()

# Load schema if necessary - we use IF NOT EXISTS so this if fine to run for sanity checking
with open(SCHEMA_FILE) as f:
    cur.executescript(f.read())

# This is used for logging
try:
    event = sys.argv[1]

    # TODO: battery name/listing/path
    name = 'BAT1'

    now = int(time.time())

    with open('/sys/class/power_supply/BAT1/cycle_count') as f:
        cycle_count = int(f.read())

    with open('/sys/class/power_supply/BAT1/charge_now') as f:
        charge_now = int(f.read())

    with open('/sys/class/power_supply/BAT1/current_now') as f:
        current_now = int(f.read())

    with open('/sys/class/power_supply/BAT1/voltage_now') as f:
        voltage_now = int(f.read())

    with open('/sys/class/power_supply/BAT1/voltage_min_design') as f:
        voltage_min_design = int(f.read())

    # Energy = Wh
    energy_now = charge_now * voltage_now # /1000000000000
    energy_min = charge_now * voltage_min_design # what uPower uses

    # Power = W
    power_now = current_now * voltage_now
    power_min = current_now * voltage_min_design

    # Write to DB
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    sql = "INSERT INTO log VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    values = (now, name, event, cycle_count, charge_now, current_now, voltage_now, voltage_min_design, energy_now, energy_min, power_now, power_min)
    cur.execute(sql, values)
    con.commit()
    con.close()

# This can be run for reporting
except:
    # No argument - print last stats
    con = sqlite3.connect(DB_FILE)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    sql = """
          SELECT * FROM log
          WHERE event = 'resume'
          ORDER BY TIME DESC
          LIMIT 1
          """
    res = cur.execute(sql)
    resume = res.fetchone()

    sql = """
          SELECT * FROM log
          WHERE event = 'suspend'
          ORDER BY TIME DESC
          LIMIT 1
          """
    res = cur.execute(sql)
    suspend = res.fetchone()

    con.close()

    # Get Time
    delta_s = resume['time'] - suspend['time']
    delta_h = Decimal(delta_s/3600)

    # Get Power Used - we use min vs now since we don't have voltage_avg / smoothing, probably safer...
    # energy_used_wh = Decimal((suspend['energy_now'] - resume['energy_now'])/1000000000000)
    energy_used_wh = Decimal((suspend['energy_min'] - resume['energy_min'])/1000000000000)

    # Average Power Use
    power_use_w = energy_used_wh / delta_h

    # Full Battery Power (presumably we should use min/nominal here?)
    with open('/sys/class/power_supply/BAT1/charge_full') as f:
        charge_full = int(f.read())
    energy_full_wh = Decimal(charge_full/1000000000000) * resume['voltage_min_design']

    # Percentage Battery Used / hour
    percent_per_h = 100 * power_use_w / energy_full_wh

    # Time left from resume
    until_empty_h = Decimal(resume['energy_min']/1000000000000)/ power_use_w


    print('Slept for {:.2f} hours'.format(delta_h))
    print('Used {:.2f} Wh, an average rate of {:.2f} W'.format(energy_used_wh, power_use_w))
    # print('At {:.2f}/Wh drain you battery would be empty in {:.2f} hours'.format(power_use_w, until_empty_h))
    print('For your {:.2f} Wh battery this is {:.2f}%/hr or {:.2f}%/day'.format(energy_full_wh, percent_per_h, percent_per_h*24))
