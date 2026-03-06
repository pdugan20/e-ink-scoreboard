# Raspberry Pi Setup Instructions

## Prerequisites

- **Hardware**: Raspberry Pi Zero 2 W + [Inky Impression 7.3"](https://shop.pimoroni.com/products/inky-impression-7-3) e-ink display
- **OS**: Raspberry Pi OS Bookworm (64-bit recommended)
- **Python**: 3.11+ (included with Bookworm)
- **Network**: WiFi connection for live score data

## Quick Install (Recommended)

For automatic setup, use the installation script:

```bash
# Clone the project
git clone https://github.com/pdugan20/e-ink-scoreboard.git
cd e-ink-scoreboard

# Run the installation script
./scripts/install.sh

# Configure your preferences (teams, timezone, theme, etc.)
./scripts/configure.sh

# Setup auto-startup services
./scripts/setup-services.sh

# Reboot to apply hardware changes
sudo reboot
```

Or run all steps at once:

```bash
git clone https://github.com/pdugan20/e-ink-scoreboard.git
cd e-ink-scoreboard
./scripts/setup.sh
```

**What the install script does:**

- Updates system packages
- Installs all dependencies (Python, graphics libraries, system monitoring)
- Configures SPI/I2C for Inky display
- Installs Pimoroni Inky library with virtual environment
- Installs your project dependencies
- Sets up Playwright for high-quality screenshots
- Creates log directories and sets up comprehensive logging
- Sets up mDNS so the scoreboard is accessible at `scoreboard.local`

**What the configure script does:**

- Sets your favorite MLB teams
- Configures timezone for game times
- Chooses refresh interval
- Selects display theme
- Enables/disables news screensaver
- Optionally sets an admin password for the web settings panel

---

## After Reboot

After rebooting, the scoreboard starts automatically. Verify everything is working:

```bash
# Check all three services are running
sudo systemctl status sports-server sports-display sports-watchdog

# Verify the web UI is accessible
curl -s http://localhost:5001/api/scores/MLB | head -c 100

# Run the full verification script
./scripts/verify-installation.sh
```

The display should update within a few minutes. If games are currently active,
you'll see live scores. If not, the screensaver will show team news.

## Manual Control Commands

To run commands manually, activate the virtual environment first:

```bash
source ~/.virtualenvs/pimoroni/bin/activate

# Update display once
python src/eink_display.py --once

# Force update (bypass game check)
python src/eink_display.py --once --force

# Use custom config file
python src/eink_display.py --config my_config.json
```

## Troubleshooting

For detailed troubleshooting steps, see **[docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md)**.

Quick diagnostics:

```bash
# Verify installation
./scripts/verify-installation.sh

# Generate full system diagnostics report
./scripts/diagnostics.sh

# Check services status
sudo systemctl status sports-server.service sports-display.service

# View recent logs
sudo journalctl -u sports-display.service --since "10 minutes ago"
tail -f ~/logs/eink_display.log

# Test display update
python src/eink_display.py --once
```

## Upgrading

To update an existing installation to the latest version:

```bash
./scripts/upgrade.sh
```

This pulls the latest code, updates Python packages and Playwright browser,
re-installs service files and sudoers rules, restarts all services, and runs
verification. Your configuration is preserved.

## Development Iteration

When developing on your Mac and deploying to the Pi, the typical workflow is:

1. **Make changes on Mac** -- edit code, run tests with `make test`
2. **Push to GitHub** -- `git push origin main`
3. **Update the Pi** -- SSH in and run the upgrade script:

```bash
ssh pi@scoreboard.local
cd ~/e-ink-scoreboard
./scripts/upgrade.sh
```

The upgrade script handles everything: pulling code, updating dependencies,
re-installing service files, and restarting all three services.

**Checking logs after an upgrade:**

```bash
# Watch display service output in real-time
sudo journalctl -u sports-display.service -f

# View application log
tail -f ~/logs/eink_display.log

# Check all three services at once
sudo systemctl status sports-server sports-display sports-watchdog
```

**Quick manual test without waiting for the refresh cycle:**

```bash
source ~/.virtualenvs/pimoroni/bin/activate
python src/eink_display.py --once --force
```

**If you change service files** (`services/*.service`), the upgrade script
automatically re-templates and reloads them. No need to manually run
`setup-services.sh` unless doing a fresh install.

## Uninstalling

To remove all services and clean up:

```bash
./scripts/uninstall.sh        # Keep virtual environment
./scripts/uninstall.sh --all  # Remove everything
```

## Accessing the Web Interface

After installation, the scoreboard is discoverable on your local network at:

- **<http://scoreboard.local:5001>** -- main display
- **<http://scoreboard.local:5001/settings>** -- configuration panel

This works automatically on macOS, iOS, and Linux. For **Windows**, mDNS
requires one of the following:

- Windows 10 1709+ (Fall Creators Update) has built-in mDNS support
- Older Windows: install [Bonjour Print Services](https://support.apple.com/kb/DL999) or iTunes (which includes Bonjour)

If `scoreboard.local` doesn't resolve, you can use the Pi's IP address
directly (find it with `hostname -I` on the Pi).

## Notes

- **Eink Display Lifespan**: Avoid refreshing more than once every 6 minutes to preserve display
- **Power**: Consider a UPS for uninterrupted operation
- **Network**: Ensure stable internet connection for live sports data
- **Storage**: Use a high-quality SD card (Class 10+) for reliability

## Support

If you encounter issues, see the **[Troubleshooting Guide](TROUBLESHOOTING.md)** for detailed diagnostic steps.
