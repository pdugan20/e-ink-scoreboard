# E-Ink Scoreboard

Display live sports scores on your e-ink display with professional quality and real-time updates!

## Features

- **Live MLB Scores**: Real-time MLB scores with on-base and out displays
- **Team News Screensaver**: Automatically displays team news when no games are scheduled
- **Clean Layout**: Optimized for 800x480 e-ink displays showing up to 15 games in a 3x5 grid
- **Auto-refresh**: Configurable refresh interval with power-saving logic
- **Mac Testing**: Full development environment with live preview
- **Raspberry Pi Ready**: Complete deployment guide

## Quick Start

### Mac Development/Testing

1. **Clone and setup**:

   ```bash
   git clone https://github.com/pdugan20/e-ink-scoreboard.git
   cd e-ink-scoreboard
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Test the display**:

   ```bash
   # Start web server (from project root)
   ./venv/bin/python src/dev_server.py --port 5001

   # Take screenshot (in another terminal, from project root)
   ./venv/bin/python src/eink_display.py --once

   # View result: test_display_output.png
   ```

3. **View in browser**:
   - Live data: http://localhost:5001/display
   - Test data: http://localhost:5001/display?test=true

### Raspberry Pi Deployment

See **[docs/RASPBERRY_PI_SETUP.md](docs/RASPBERRY_PI_SETUP.md)** for complete installation instructions.

For additional Inky Impression setup guidance, see the official **[Getting Started with Inky Impression](https://learn.pimoroni.com/article/getting-started-with-inky-impression)** guide.

## Configuration

Edit `src/eink_config.json` to customize:

```json
{
  "web_server_url": "http://localhost:5001/display",
  "display_width": 800,
  "display_height": 480,
  "screenshot_scale": 2,
  "refresh_interval": 300,
  "max_retries": 3,
  "retry_delay": 5
}
```

**Refresh Intervals:**

- **120 seconds (2m)** - Live action
- **300 seconds (5m)** - Default, good for active games
- **900 seconds (15m)** - Balanced for general use
- **1800 seconds (30m)** - Conservative, preserves display life

## Technical Details

### Data Sources

- **Live MLB data**: ESPN API with real-time scores and game status

## Project Structure

```
src/                       # Core application files
├── assets/                # Images and logos
│   └── logos/             # Team and league logos
├── static/                # CSS, JS, and static assets
│   ├── js/                # JavaScript modules
│   │   └── constants/     # Team data and constants
│   └── styles/            # CSS stylesheets
└── test-data/             # Test game data

scripts/                   # Installation and setup scripts
├── install.sh             # Raspberry Pi installation
├── configure.sh           # Interactive configuration
└── setup_services.sh      # Systemd service setup

docs/                      # Documentation
├── RASPBERRY_PI_SETUP.md  # Pi setup guide
└── TROUBLESHOOTING.md     # Common issues and fixes
```

## Commands

```bash
# Single update (looks if there are live games)
./venv/bin/python src/eink_display.py --once

# Force update (bypasses check for live games)
./venv/bin/python src/eink_display.py --once --force

# Custom server URL
./venv/bin/python src/eink_display.py --url http://localhost:5001/display

# Custom server with dummy data
./venv/bin/python src/eink_display.py --url http://localhost:5001/display?test=true --once

# Generate dithered preview
./venv/bin/python src/eink_display.py --url http://localhost:5001/display --once --dithering

# Test screensaver on e-ink display
./venv/bin/python src/eink_display.py --url http://localhost:5001/display?screensaver=true --once
```

## Display Update Logic

The system uses intelligent update logic to minimize e-ink wear:

- **New game day**: Updates once to show upcoming games
- **During games**: Regular updates every 2-5 minutes while games are active
- **Games scheduled only**: Skips updates to preserve display longevity

**Force an update**: Use `--once` flag or restart the display service on Raspberry Pi.

## Development

- **Preview**: http://localhost:5001/ (dev controls)
- **Clean display**: http://localhost:5001/display (screenshot target)
- **Test data**: http://localhost:5001/display?test=true (sample data)
- **Test screensaver**: http://localhost:5001/display?screensaver=true (force screensaver mode)
- **Hot reload**: Auto-refresh on file changes
- **Live data**: Fetch button to get current MLB scores

## Hardware Requirements

- **[Raspberry Pi Zero 2 W](https://shop.pimoroni.com/products/raspberry-pi-zero-2-w)** - Recommended for compact, low-power operation
- **[Inky Impression 7.3"](https://shop.pimoroni.com/products/inky-impression-7-3?variant=55186435244411)** - 7-color E Ink display (800x480)
- MicroSD card (16GB+ recommended)
- Micro USB power supply for Pi Zero 2 W

## Software Requirements

- Python 3.8+
- Raspberry Pi OS Bookworm or later
- Playwright (for high-quality screenshots)
- Flask (web server)
- Pillow (image processing)
- Inky library (Raspberry Pi E Ink display driver)

## Roadmap

### Planned Features

- **Expanded Team RSS Feeds** - News screensaver support for all 30 MLB teams
- **Dark Mode Theme** - High-contrast dark theme optimized for e-ink displays
- **NFL Support** - Full NFL game scores and schedules during football season
- **College Football (CFB) Support** - Major college football games and conferences
- **Additional E-ink Display Support** - Support for different display sizes and manufacturers
- **Web Configuration** - Browser-based setup instead of command-line configuration

### Contributions Welcome

This project is open to contributions! Areas where help is especially appreciated:

- **API Integration** - Integration with additional data sources
- **Hardware Support** - Testing on different e-ink displays and dimensions
- **Documentation** - Setup guides and troubleshooting

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
