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

   # Use requirements-dev.txt for Mac (excludes Pi-specific hardware packages)
   pip install -r requirements-dev.txt
   playwright install chromium
   ```

   **Note:** Mac development uses `requirements-dev.txt` which excludes the `inky` package and its dependencies (`spidev`, `gpiod`) since these are Linux-only hardware libraries for the Raspberry Pi.

2. **Test the display**:

   ```bash
   # Activate virtual environment first
   source venv/bin/activate

   # Start web server (from project root)
   python src/dev_server.py --port 5001

   # Take screenshot (in another terminal, from project root)
   python src/eink_display.py --once

   # View result: test_display_output.png
   ```

3. **View in browser**:
   - Live data: http://localhost:5001/display
   - Test data: http://localhost:5001/display?test=true

### Raspberry Pi Deployment

See **[docs/RASPBERRY_PI_SETUP.md](docs/RASPBERRY_PI_SETUP.md)** for complete installation instructions.

**Note:** Raspberry Pi uses the full `requirements.txt` which includes the `inky` display library and hardware dependencies.

For additional Inky Impression setup guidance, see the official **[Getting Started with Inky Impression](https://learn.pimoroni.com/article/getting-started-with-inky-impression)** guide.

## API Documentation

The project provides REST API endpoints for sports scores and team news:

- **[API Reference](docs/API.md)** - Complete API documentation with endpoint specifications and response formats
- **[API Examples](docs/API_EXAMPLES.md)** - Testing examples, sample responses, and troubleshooting guides

**Key Endpoints:**

- `/api/scores/MLB` - Live MLB game scores and standings
- `/api/screensaver/MLB` - Team news articles for screensaver mode
- `/display` - E-ink optimized display page

## Configuration

Edit `src/eink_config.json` to customize:

```json
{
  "web_server_url": "http://localhost:5001/display",
  "display_width": 800,
  "display_height": 480,
  "screenshot_scale": 2,
  "refresh_interval": 360,
  "max_retries": 3,
  "retry_delay": 5
}
```

**Refresh Intervals:**

- **360 seconds (6m)** - Default, good for active games
- **900 seconds (15m)** - Balanced for general use
- **1800 seconds (30m)** - Conservative, preserves display life

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
└── setup-services.sh      # Systemd service setup

docs/                      # Documentation
├── API.md                 # API endpoints and responses
├── API_EXAMPLES.md        # API testing examples and guides
├── RASPBERRY_PI_SETUP.md  # Pi setup guide
└── TROUBLESHOOTING.md     # Common issues and fixes
```

## Commands

```bash
# Activate virtual environment first
source venv/bin/activate

# Single update (looks if there are live games)
python src/eink_display.py --once

# Force update (bypasses check for live games)
python src/eink_display.py --once --force

# Custom server URL
python src/eink_display.py --url "http://localhost:5001/display"

# Custom server with dummy data
python src/eink_display.py --url "http://localhost:5001/display?test=true" --once

# Generate dithered preview
python src/eink_display.py --url "http://localhost:5001/display" --once --dithering

# Test screensaver (requires --force to bypass game check)
python src/eink_display.py --url "http://localhost:5001/display?screensaver=true" --once --force
```

## Display Update Logic

The system uses intelligent update logic to minimize e-ink wear:

- **New game day**: Updates once to show upcoming games
- **During games**: Regular updates every 6 minutes while games are active
- **Games scheduled only**: Skips updates to preserve display longevity

**Force an update**: Use `--once` flag or restart the display service on Raspberry Pi.

## Development

### Code Quality Checks

#### Automatic Checks (GitHub Actions)

All pushes and PRs are automatically checked for code quality using Black, Ruff, Prettier, and ESLint.

#### Local Development Setup

1. **Enable pre-commit hooks** (recommended):

   ```bash
   ./scripts/setup-hooks.sh
   ```

   This will automatically run all checks before each commit.

2. **Manual checks**:
   ```bash
   ./scripts/check-all.sh  # Run all checks
   black .                 # Format Python code
   ruff check --fix .      # Fix Python linting issues
   npx prettier --write .  # Format JS/TS/JSON files
   npx eslint --fix .      # Fix JavaScript linting issues
   ```

- **Preview**: http://localhost:5001/ (dev controls)
- **Clean display**: http://localhost:5001/display (screenshot target)
- **Test data**: http://localhost:5001/display?test=true (sample data)
- **Test screensaver**: http://localhost:5001/display?screensaver=true (force screensaver mode)
- **Hot reload**: Auto-refresh on file changes
- **Live data**: Fetch button to get current MLB scores

**Configuration**: Code quality settings are defined in `pyproject.toml`

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
- Psutil (system monitoring and resource management)

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
