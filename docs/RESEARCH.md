# Suspend And Battery Research

## Batterylog Findings

- Database inspected: `/opt/batterylog/batterylog.db`
- Pairing method: adjacent `suspend -> resume` rows only
- Useful filter for sleep efficiency:
  - sleep duration `>= 1h`
  - net battery discharge only
  - exclude net battery gain sessions, which are charging sessions in practice

### Recent Sleep Efficiency

From the last 60 days of filtered non-charging suspend sessions:

- session count: `50`
- mean drain: `0.24 W`
- median drain: `0.22 W`
- mean battery loss: `0.37%/hr`
- median battery loss: `0.35%/hr`

Interpretation:

- normal suspend on this machine is roughly `0.22-0.23 W`
- that is about `0.35%/hr`
- an 8 hour overnight suspend is about `2.8%`
- a 10 hour overnight suspend is about `3.5%`

This baseline looks reasonable. The problem is not the typical overnight result. The only notable issue is a small number of outliers.

### Recent Outliers

Examples of higher non-charging sessions in the last 60 days:

- `2026-03-07 20:12 -> 2026-03-07 23:15`: `0.89 W`, `1.39%/hr`
- `2026-03-01 19:38 -> 2026-03-01 09:14`: `0.40 W`, `0.62%/hr`
- `2026-03-10 05:13 -> 2026-03-10 15:20`: `0.34 W`, `0.53%/hr`

There are also many sessions tightly clustered around `0.20-0.23 W`, which supports the view that these are outliers rather than the normal suspend behavior.

### Negative "Used X Wh" Sessions

The current `batterylog.py` last-cycle report prints negative usage when the battery has more energy at resume than it had at suspend.

That is mathematically correct, but semantically misleading. In practice those negative sessions are charging sessions and should be excluded when evaluating suspend efficiency.

## s2idle / S0ix Findings

This machine is using `s2idle`, not deep sleep:

- `/sys/power/mem_sleep` reports: `[s2idle] deep`
- kernel reported: `Low-power S0 idle used by default for system suspend`

This means a bad suspend session can come from two different classes of failure:

1. Something actually wakes the machine during suspend.
2. The machine stays suspended, but some device or driver prevents good low-power residency, so power draw stays higher than normal.

### What The Outliers Look Like

Spot checks of recent outliers did not show obvious wake storms in the journal.

Checked sessions:

- `2026-03-07 20:12 -> 2026-03-07 23:15`
- `2026-02-28 19:38 -> 2026-03-01 09:14`

Both looked like:

- one suspend entry
- one suspend exit
- no obvious repeated wake/suspend cycling in the middle

That points more toward poor low-power residency than repeated full wakes.

### Likely Contributors To Outliers

Based on the current machine state, the likely classes to watch are:

- USB / XHCI
- Thunderbolt
- RTC / alarm timers
- lid / power button wake sources
- sometimes Wi-Fi or Bluetooth

Observed details:

- `/proc/acpi/wakeup` has several wake-capable devices enabled
- many `/sys/.../power/wakeup` entries are enabled
- `thunderbolt-sleep.sh` failed during some suspends with `Module thunderbolt is in use`

The Thunderbolt failure is a suspect, not proof. It appeared in outlier sessions, but it also needs correlation with good sessions before blaming it directly.

### What Is Trackable Right Now

The current machine exposes enough state to investigate future outliers, but not enough from the current batterylog database alone to attribute old outliers precisely.

What batterylog currently tells us:

- when suspend started
- when resume happened
- how much energy changed across that interval

What it does not currently tell us:

- AC / charger state at suspend and resume
- which wake sources were enabled
- which inhibitor was active
- whether low-power S0 residency was good or poor
- whether a device caused repeated partial wakeups

Current host limitations:

- `/sys/kernel/debug/wakeup_sources` is not available here
- low-power residency files exist under `/sys/devices/system/cpu/cpuidle/`, but they were `0` when checked and are not yet integrated into logging

Practical conclusion:

- historical outliers can be identified
- exact root cause needs additional logging around future suspend/resume events

## Niri Suspend Flow

### Idle Suspend

Idle suspend is triggered from the Niri config, not from batterylog.

Relevant config:

- `~/.config/niri/config.kdl`
- line showing the idle timeout path:
  - `swayidle ... timeout 900 niri-idle-suspend ...`

Meaning:

- lock after 5 minutes
- power off monitors after 5.5 minutes
- attempt suspend after 15 minutes of idle

`niri-idle-suspend` is therefore an idle-timeout gatekeeper, not a low-battery handler.

### What `niri-idle-suspend` Checks

Script path:

- `/home/lhl/bin/niri-idle-suspend`

Enabled checks from `~/.config/niri/suspend.conf`:

- AC power
- active audio streams
- system load above `3.0`
- active SSH sessions
- DBus idle inhibitors
- manual inhibit file `~/.cache/niri-no-suspend`

Important behavior:

- if any check blocks, the script exits without suspending
- otherwise it runs `systemctl suspend`

### Is Video Playback Already Blocking Idle Suspend?

Probably yes, at least for the idle-timeout path.

Reasons:

- `CHECK_AUDIO=yes`
- `CHECK_VIDEO_INHIBIT=yes`
- journal already shows multiple real blocks such as:
  - `BLOCKED: idle inhibitor active via dbus (2)`
  - `BLOCKED: on AC power (ADP1)`
  - `BLOCKED: system load ... exceeds threshold`

This means your idle suspend path is already set up to avoid suspending in some active-use cases, including cases where an app sets an idle inhibitor.

Important caveat:

- the video check is generic and counts `idle` inhibitors via `login1`
- it does not identify which app created the inhibitor
- whether a browser/video site inhibits correctly depends on the application actually setting the inhibitor

## Low-Battery Suspend Flow

There is a separate low-battery suspend script:

- `~/.local/bin/niri-battery-suspend`

This is started from Niri config via:

- `spawn-at-startup "niri-battery-suspend"`

### What It Does

- polls battery status every 30 seconds
- warns at `<= 10%`
- suspends after 60 seconds unless cancelled
- at `<= 5%`, warns and suspends after 60 seconds with no cancel path
- before the final suspend at the warning threshold, it re-checks battery status and only suspends if still `Discharging`

### Does Low-Battery Suspend Respect Video Playback?

No.

`niri-battery-suspend` does not check:

- idle inhibitors
- audio playback
- fullscreen/video state
- manual inhibit file
- SSH
- system load

It only checks battery state and whether the battery is still discharging.

Practical result:

- idle suspend is already somewhat protected against playback and active use
- low-battery suspend is not protected against playback and will still suspend after its timeout if the battery remains low and discharging

## Current Conclusion

- typical suspend efficiency on this machine is good
- outliers exist, but they do not currently look like obvious wake storms
- the machine is using `s2idle`, so poor low-power residency is a strong candidate for bad sessions
- the current idle suspend path already tries to avoid suspending during active use
- the current low-battery suspend path does not

## Suggested Future Logging

If future root-cause work is needed, the most useful additions around suspend/resume would be:

- AC state at suspend and resume
- a snapshot of active `login1` inhibitors
- enabled wake sources from `/proc/acpi/wakeup` and `/sys/.../power/wakeup`
- a journal slice around suspend/resume
- any reliable low-power S0 residency counter available on this kernel
