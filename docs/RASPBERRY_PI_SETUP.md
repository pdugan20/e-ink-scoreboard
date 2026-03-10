# Raspberry Pi Setup Guide

This guide walks you through the complete setup process, from a bare SD card
to a working scoreboard on your wall.

> **Already have a booted Pi?** Skip to [Part 3: Install the Scoreboard](#part-3-install-the-scoreboard).

## What You'll Need

### Required Hardware

- **[Raspberry Pi Zero 2 W](https://shop.pimoroni.com/products/raspberry-pi-zero-2-w)** -
  Must be the Zero 2 W (with WiFi). The original Zero won't work (too slow).
- **[Inky Impression 7.3"](https://shop.pimoroni.com/products/inky-impression-7-3?variant=55186435244411)** -
  800x480 e-ink display. Connects directly to the GPIO header.
- **MicroSD Card** - 16GB minimum, 32GB recommended. Use a Class 10 or better
  card from a reputable brand (SanDisk, Samsung).
- **USB-C Power Supply** - 5V 2.5A minimum. The official Raspberry Pi power
  supply is recommended.

### Before You Start

Have the following ready:

- **WiFi network name (SSID)** and **password** - Pi Zero 2 W only supports
  2.4GHz WiFi (not 5GHz)
- **A computer** with an SD card reader (or USB adapter) for flashing
- **Your timezone** - for displaying game times correctly

## Part 1: Flash the SD Card

### Download Raspberry Pi Imager

Download and install from
[raspberrypi.com/software](https://www.raspberrypi.com/software/). Available
for macOS, Windows, and Linux.

### Flash the Card

1. Insert your microSD card into your computer
2. Open Raspberry Pi Imager
3. **Choose Device**: Raspberry Pi Zero 2 W
4. **Choose OS**: Raspberry Pi OS (other) > **Raspberry Pi OS Lite (64-bit)**
   - Must be Bookworm or later (includes Python 3.11+)
   - Lite is recommended since the scoreboard runs headless (no desktop needed)
5. **Choose Storage**: Select your microSD card

### Configure OS Settings

**Before clicking Write**, click **Edit Settings** (or the gear icon). This is
the most important step - it configures WiFi, SSH, and the hostname so you can
connect to the Pi on first boot.

**General tab:**

| Setting                | Value                           | Why                                              |
| ---------------------- | ------------------------------- | ------------------------------------------------ |
| Set hostname           | `scoreboard`                    | Makes the Pi accessible at `scoreboard.local`    |
| Set username           | `pi`                            | Standard username for all commands in this guide |
| Set password           | (your choice)                   | You'll need this to SSH in                       |
| Configure wireless LAN | Your WiFi SSID + password       | Pi connects automatically on boot                |
| Wireless LAN country   | Your country code (e.g., US)    | Required for WiFi to work                        |
| Set locale settings    | Your timezone + keyboard layout | Game times display correctly                     |

**Services tab:**

| Setting    | Value                            |
| ---------- | -------------------------------- |
| Enable SSH | Yes, use password authentication |

Click **Save**, then **Write**. Confirm you want to erase the card. Wait 3-5
minutes for the write and verification to complete.

**If your Mac shows "disk not readable"** when you insert the SD card, click
Ignore. Raspberry Pi Imager handles the formatting.

## Part 2: First Boot and SSH

### Boot the Pi

1. Insert the flashed microSD card into the Raspberry Pi
2. Connect the Inky display to the GPIO header (align the pins, press gently
   until fully seated - no soldering required)
3. Plug in the USB-C power supply

The first boot takes 1-2 minutes. The green LED will flash as it starts up.

### Find the Pi on Your Network

After 1-2 minutes, the Pi should be on your network. Try connecting:

**macOS or Linux:**

```bash
ping scoreboard.local
```

If you see replies, the Pi is online. Press Ctrl+C to stop.

**If `scoreboard.local` doesn't resolve:**

- Wait another minute (first boot can be slow)
- Check your router's admin panel for a device named "scoreboard" and note its
  IP address
- On Windows, mDNS may require
  [Bonjour Print Services](https://support.apple.com/kb/DL999) or Windows 10
  1709+

### Connect via SSH

```bash
ssh pi@scoreboard.local
```

- Type `yes` to accept the SSH fingerprint (first time only)
- Enter the password you set in Raspberry Pi Imager
- You should see: `pi@scoreboard:~ $`

If using an IP address instead: `ssh pi@192.168.1.xxx` (replace with actual IP).

### First Boot Troubleshooting

**SSH connection refused:**

- Wait 2 full minutes after power-on (first boot is slow)
- Verify SSH was enabled in Imager settings
- Re-flash the SD card if needed, double-checking the settings

**WiFi won't connect:**

- Pi Zero 2 W only supports 2.4GHz WiFi, not 5GHz
- Double-check SSID and password (case-sensitive)
- Verify your router isn't blocking new devices
- Some routers have separate 2.4GHz and 5GHz network names - use the 2.4GHz one

## Part 3: Install the Scoreboard

Once you're connected via SSH, install git (not included in Raspberry Pi OS
Lite), clone the project, and run the setup script:

```bash
sudo apt update && sudo apt install -y git
git clone https://github.com/pdugan20/e-ink-scoreboard.git
cd e-ink-scoreboard
./scripts/setup.sh
```

This runs three stages automatically:

### Stage 1: Installation (`install.sh`)

Installs all system dependencies, hardware drivers, and Python packages:

- Updates system packages
- Enables SPI and I2C interfaces for the e-ink display
- Installs the Pimoroni Inky display library (creates venv at
  `~/.virtualenvs/pimoroni`)
- Installs Python dependencies
- Installs Playwright and Chromium for screenshot capture
- Sets up mDNS so the scoreboard is accessible at `scoreboard.local`
- Creates log directories

This stage takes the longest - expect 15-30 minutes on the Pi Zero 2 W,
primarily for Playwright/Chromium installation.

### Stage 2: Configuration (`configure.sh`)

Interactive prompts to set your preferences:

- **Favorite MLB teams** - select one or more teams to highlight
- **Timezone** - for displaying game times
- **Refresh interval** - how often the display updates (6, 15, or 30 minutes)
- **Display theme** - Default, Team Colors, or MLB Scoreboard
- **Screensaver** - show team news when no games are scheduled
- **Admin password** - optional password protection for the settings panel

### Stage 3: Services (`setup-services.sh`)

Installs three systemd services that run the scoreboard automatically:

- **sports-server** - Flask web server on port 5001
- **sports-display** - E-ink display controller
- **sports-watchdog** - Health monitor with automatic recovery

Also sets up a daily 4 AM reboot for memory management. See
[SERVICES.md](SERVICES.md) for detailed service documentation.

### Reboot

After setup completes, reboot to apply hardware changes (SPI/I2C):

```bash
sudo reboot
```

This is required - the display hardware won't work until after a reboot.

## Part 4: Verify and Use

After the Pi reboots (~60 seconds), SSH back in:

```bash
ssh pi@scoreboard.local
cd e-ink-scoreboard
```

### Check Services

All three services should be running:

```bash
sudo systemctl status sports-server sports-display sports-watchdog
```

You should see `active (running)` for each service.

### Run Verification

The verification script checks hardware, software, and service health:

```bash
./scripts/verify-installation.sh
```

All critical checks should pass. Warnings about optional components are normal.

### Access the Web Interface

Open a browser on any device on your network:

- **Scoreboard display**: <http://scoreboard.local:5001>
- **Settings panel**: <http://scoreboard.local:5001/settings>

From the settings panel you can change teams, themes, timezone, refresh
interval, WiFi networks, and more - no SSH required.

**Windows users:** If `scoreboard.local` doesn't resolve, use the Pi's IP
address instead. Find it with `hostname -I` on the Pi.

### Force a Display Update

The display updates automatically based on the game schedule. To trigger an
immediate update:

```bash
source ~/.virtualenvs/pimoroni/bin/activate
python src/eink_display.py --once --force
```

If games are currently active, you'll see live scores. If not, the screensaver
shows team news (if enabled).

## Maintenance

### Manual Commands

Always activate the virtual environment first:

```bash
source ~/.virtualenvs/pimoroni/bin/activate

python src/eink_display.py --once              # Single update
python src/eink_display.py --once --force      # Force update (bypass game check)
python src/eink_display.py --once --dithering  # Generate dithered preview
```

### Upgrading

To update to the latest version:

```bash
./scripts/upgrade.sh
```

This pulls the latest code, updates dependencies, re-installs service files,
restarts all services, and runs verification. Your configuration is preserved.

### Development Workflow

When developing on your Mac and deploying to the Pi:

1. **Make changes on Mac** - edit code, run tests with `make test`
2. **Push to GitHub** - `git push origin main`
3. **Update the Pi** - SSH in and run:

```bash
cd ~/e-ink-scoreboard
./scripts/upgrade.sh
```

### Diagnostics

If something isn't working:

```bash
# Full system diagnostics report
./scripts/diagnostics.sh

# View recent logs
sudo journalctl -u sports-display.service --since "10 minutes ago"
tail -f ~/logs/eink_display.log
```

See the **[Troubleshooting Guide](TROUBLESHOOTING.md)** for detailed solutions
to common issues.

### Uninstalling

```bash
./scripts/uninstall.sh        # Remove services, keep virtual environment
./scripts/uninstall.sh --all  # Remove everything
```

## Notes

- **E-ink display lifespan**: Avoid refreshing more than once every 6 minutes
  to preserve the display
- **Power**: Consider a UPS for uninterrupted operation during power outages
- **Network**: Ensure a stable internet connection for live score data
- **Storage**: Use a high-quality SD card (Class 10+) for reliability
- **Daily reboot**: The system reboots at 4 AM daily for memory management
