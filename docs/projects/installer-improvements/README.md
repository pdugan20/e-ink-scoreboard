# Installer Improvements

Harden the Raspberry Pi CLI installer to be robust, user-friendly, and
recoverable.

## Background

The e-ink scoreboard installs on Raspberry Pi via three bash scripts run in
sequence:

1. `scripts/install.sh` -- system packages, hardware config, Python deps,
   Playwright
2. `scripts/configure.sh` -- interactive prompts for teams, timezone, theme,
   network
3. `scripts/setup-services.sh` -- systemd services, cron jobs, auto-startup

This works for straightforward setups but has failure modes with poor recovery.
The installer assumes every step succeeds, offers no verification, and cannot
be safely re-run or rolled back.

## Goals

- Users can verify their installation actually works before rebooting
- Scripts detect already-completed steps and skip them (safe to re-run)
- Critical failures stop the installer with clear error messages
- Users can uninstall cleanly or upgrade an existing installation
- Documentation is accurate and references the correct project

## Current Issues

| Issue | Impact |
|---|---|
| No post-install verification | Silent partial failures cause confusing runtime errors |
| Playwright/Chromium can fail silently | Display service starts but crashes |
| Pimoroni venv checked by directory, not function | Reinstalls unnecessarily or uses broken venv |
| Static IP setup modified `/etc/dhcpcd.conf` | Removed -- mDNS discovery replaces static IP |
| Scripts not idempotent | Re-running can duplicate cron jobs, recreate services |
| Log dirs mismatch actual log paths | `/var/log/eink-display`, `/tmp/eink-logs`, `~/logs/` all created but only one used |
| `RASPBERRY_PI_SETUP.md` references old repo name | Confusing for new users |
| ~~`enhanced_watchdog.py` exists but unused~~ | Resolved: merged into `watchdog_monitor.py` |
| No uninstall or upgrade path | Users must manually clean up |

## Key Files

| File | Role |
|---|---|
| `scripts/install.sh` | Main installation script |
| `scripts/configure.sh` | Interactive configuration |
| `scripts/setup-services.sh` | Systemd service setup |
| `services/sports-server.service` | Flask web server template |
| `services/sports-display.service` | Display controller template |
| `services/sports-watchdog.service` | Watchdog monitor template |
| `docs/RASPBERRY_PI_SETUP.md` | Setup documentation |
| `src/eink_config.json` | Runtime configuration |
| `src/static/js/config.js` | Frontend configuration |

## Tracker

See [TRACKER.md](TRACKER.md) for the phased task list.
