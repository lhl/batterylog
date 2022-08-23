#!/usr/bin/python

from   decimal import Decimal
import sqlite3
import sys
import time

DB_PATH = 'batterylog.db'

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
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    sql = "INSERT INTO log VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    values = (now, name, event, cycle_count, charge_now, current_now, voltage_now, voltage_min_design, energy_now, energy_min, power_now, power_min)
    cur.execute(sql, values)
    con.commit()
    con.close()

# This can be run for reporting
except:
    # No argument - print last stats
    con = sqlite3.connect(DB_PATH)
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

    # Get Power Used - we use now vs min since that's more accurate
    power_used_wh = Decimal((suspend['power_now'] - resume['power_now'])/1000000000000)

    # Average Energy Use
    energy_use_w = power_used_wh / delta_h

    # Full Battery Power
    with open('/sys/class/power_supply/BAT1/charge_full') as f:
        charge_full = int(f.read())
    power_full_wh = percent_per_h = Decimal(charge_full/1000000000000) * resume['voltage_min_design']

    # Percentage Battery Used / hour
    percent_per_h = 100 * energy_use_w / power_full_wh


    print('Slept for {:.2f} hours'.format(delta_h))
    print('Used {:.2f} Wh, an average rate of {:.2f} W'.format(power_used_wh, energy_use_w))
    print('For your {:.2f} Wh battery this is {:.2f}%/hr or {:.2f}%/day'.format(power_full_wh, percent_per_h, percent_per_h*24))
