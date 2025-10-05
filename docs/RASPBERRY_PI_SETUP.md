# Raspberry Pi Setup Instructions

## Quick Install (Recommended)

For automatic setup, use the installation script:

```bash
# Clone the project
git clone https://github.com/pdugan20/sports-scores-plugin.git
cd sports-scores-plugin

# Run the installation script
./scripts/install.sh

# Configure your preferences (teams, timezone, theme, static IP, etc.)
./scripts/configure.sh

# Setup auto-startup services
./scripts/setup-services.sh

# Reboot to apply hardware changes
sudo reboot
```

**What the install script does:**

- Updates system packages
- Installs all dependencies (Python, graphics libraries, system monitoring)
- Configures SPI/I2C for Inky display
- Installs Pimoroni Inky library with virtual environment
- Installs your project dependencies
- Sets up Playwright for high-quality screenshots
- Creates log directories and sets up comprehensive logging

**What the configure script does:**

- Sets your favorite MLB teams
- Configures timezone for game times
- Chooses refresh interval
- Selects display theme
- Enables/disables news screensaver
- **Optionally sets a static IP** (recommended for reliable SSH access)

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
# Check services status
sudo systemctl status sports-server.service sports-display.service

# View recent logs
sudo journalctl -u sports-display.service --since "10 minutes ago"

# Test display update
python src/eink_display.py --once
```

## Notes

- **Eink Display Lifespan**: Avoid refreshing more than once every 6 minutes to preserve display
- **Power**: Consider a UPS for uninterrupted operation
- **Network**: Ensure stable internet connection for live sports data
- **Storage**: Use a high-quality SD card (Class 10+) for reliability

## Support

If you encounter issues, see the **[Troubleshooting Guide](TROUBLESHOOTING.md)** for detailed diagnostic steps.
