# Installer Improvements -- Tracker

## Phase 1: Verification and Diagnostics

Add a verification script that confirms the installation actually works.

- [x] Create `scripts/verify-installation.sh` with checks for:
  - [x] Pimoroni Inky library imports successfully in Python
  - [x] Playwright and Chromium are installed and functional
  - [x] SPI kernel module is loaded (`/dev/spidev0.0` exists)
  - [x] I2C interface is enabled
  - [x] Flask server starts and responds on port 5001
  - [x] All three systemd services are enabled
  - [x] Log directories exist with correct permissions
  - [x] `eink_config.json` is valid JSON
  - [x] `config.js` is syntactically valid
- [x] Call `verify-installation.sh` at the end of `install.sh`
- [x] Add `--check` flag to `install.sh` to run verification standalone

## Phase 2: Idempotency and Error Handling

Make scripts safe to re-run and fail clearly on errors.

- [x] `install.sh` -- detect already-completed steps:
  - [x] Skip `apt update/upgrade` if `--skip-update` flag passed
  - [x] Check if SPI/I2C already enabled before running `raspi-config`
  - [x] Check if Pimoroni venv is functional (import inky) before reinstalling
  - [x] Check if Playwright Chromium already installed before reinstalling
- [x] Add `set -e` with proper error trapping to all scripts
- [x] Add error checking after each critical operation:
  - [x] `apt install` package groups
  - [x] `pip install` requirements
  - [x] Playwright install
  - [x] Pimoroni library clone and install
- [x] `configure.sh` -- removed static IP setup (replaced by mDNS discovery)
- [x] `configure.sh` -- validate user input before writing config files
- [x] `setup-services.sh` -- check if services already exist before creating

## Phase 3: Recovery and Maintenance

Add scripts for uninstalling and upgrading.

- [x] Create `scripts/uninstall.sh`:
  - [x] Stop and disable all three systemd services
  - [x] Remove service files from `/etc/systemd/system/`
  - [x] Remove daily reboot cron job
  - [x] Remove log directories
  - [x] Optionally remove Pimoroni venv (`~/.virtualenvs/pimoroni`)
  - [x] ~~Optionally restore `/etc/dhcpcd.conf` from backup~~ (removed with static IP)
  - [x] Print summary of what was removed
- [x] Create `scripts/upgrade.sh`:
  - [x] Pull latest code from git
  - [x] Reinstall Python dependencies
  - [x] Restart all three services
  - [x] Run verification script
  - [x] Print changelog or diff summary
- [x] Make `setup-services.sh` idempotent:
  - [x] Check for existing service files before copying
  - [x] Use `systemctl daemon-reload` after any changes
  - [x] Avoid duplicate cron entries (current check is fragile)

## Phase 4: UX Polish

Improve the user experience of running the installer.

- [x] Add shared output helper functions (source from common file):
  - [x] `info()`, `success()`, `warn()`, `error()` with consistent formatting
  - [x] Progress indicator: `[Step X/Y]` prefix
- [x] Add `--help` flag to all three scripts with usage info
- [x] Print summary at end of each script:
  - [x] What succeeded
  - [x] What failed or was skipped
  - [x] What to do next (next script to run)
- [x] Fix stale references in `docs/RASPBERRY_PI_SETUP.md`:
  - [x] Update repo name from `sports-scores-plugin` to `e-ink-scoreboard`
  - [x] Verify all paths and commands are current
- [ ] Add estimated time for each script in the setup docs
- [x] Add a top-level `scripts/setup.sh` that chains all three scripts in order

## Phase 5: Logging and Diagnostics

Clean up logging configuration and add a diagnostics tool.

- [x] Fix log directory mismatch:
  - [x] Audit which log paths are actually used at runtime
  - [x] Remove creation of unused log directories from `install.sh`
  - [x] Ensure `eink_config.json` logging path matches what `install.sh` creates
- [x] Create `scripts/diagnostics.sh`:
  - [x] Collect Pi model, OS version, kernel version
  - [x] Show memory/disk usage
  - [x] Show status of all three services
  - [x] Show recent log entries
  - [x] Show SPI/I2C status
  - [x] Show network configuration
  - [x] Output to a file for easy sharing in bug reports
- [x] Resolve `enhanced_watchdog.py` vs `watchdog_monitor.py`:
  - [x] Determine which is the intended watchdog implementation
  - [x] Remove the unused one or document when each is used
  - [x] Ensure service file references the correct script

> **Resolved:** Replaced `watchdog_monitor.py` with the enhanced version
> (5 health checks: screenshot, heartbeat, process, resources, logs).
> Deleted `enhanced_watchdog.py`. Class renamed to `WatchdogMonitor`.
> All service file references unchanged (still point to `watchdog_monitor.py`).
