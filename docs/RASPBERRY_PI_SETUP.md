# Raspberry Pi Setup Instructions

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

## Test the Setup

The installation script creates default configuration files. You can customize them later with `./scripts/configure.sh`.

## Manual Control Commands

```bash
# Update display once
python src/eink_display.py --once

# Update with custom interval (in seconds)
python src/eink_display.py --interval 600  # 10 minutes

# Use custom config file
python src/eink_display.py --config my_config.json

# Update with custom server URL
python src/eink_display.py --url http://localhost:5002/display
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

This pulls the latest code, updates dependencies, and restarts services.
Your configuration is preserved.

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
