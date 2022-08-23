CREATE TABLE IF NOT EXISTS "log" (
	"time"	INTEGER,
	"name"	TEXT,
        "event" TEXT,
	"cycle_count"	INTEGER,
	"charge_now"	INTEGER,
	"current_now"	INTEGER,
	"voltage_now"	INTEGER,
	"voltage_min_design"	INTEGER,
	"energy_now"	INTEGER,
	"energy_min"	INTEGER,
	"power_now"	INTEGER,
	"power_min"	INTEGER,
	PRIMARY KEY("time")
);
