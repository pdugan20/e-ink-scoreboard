# E-Ink Scoreboard

[![CI](https://github.com/pdugan20/e-ink-scoreboard/workflows/CI/badge.svg)](https://github.com/pdugan20/e-ink-scoreboard/actions)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Real-time MLB scores on a Pimoroni Inky e-ink display with auto-refresh and team news screensaver.

## Features

- **Live MLB Scores** - Real-time scores with on-base and out displays
- **Team News Screensaver** - Displays team news when no games are scheduled
- **Clean Layout** - Optimized for 800x480 e-ink displays, up to 15 games in a 3x5 grid
- **Auto-refresh** - Configurable refresh interval with power-saving logic
- **Mac Testing** - Full development environment with live preview
- **Raspberry Pi Ready** - Complete deployment guide

## Quick Start

### Mac Development

```bash
git clone https://github.com/pdugan20/e-ink-scoreboard.git
cd e-ink-scoreboard
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
playwright install chromium
```

```bash
# Start web server
python src/dev_server.py --port 5001

# Take screenshot (in another terminal)
python src/eink_display.py --once

# View result: test_display_output.png
```

- Live data: <http://localhost:5001/display>
- Test data: <http://localhost:5001/display?test=true>

### Raspberry Pi

See [docs/RASPBERRY_PI_SETUP.md](docs/RASPBERRY_PI_SETUP.md) for complete installation instructions.

## Commands

```bash
source venv/bin/activate

python src/eink_display.py --once              # Single update
python src/eink_display.py --once --force      # Force update (bypass game check)
python src/eink_display.py --once --dithering  # Generate dithered preview
```

## API

- `/api/scores/MLB` - Live game scores
- `/api/screensaver/MLB` - Team news articles
- `/display` - E-ink optimized display page

See [docs/API.md](docs/API.md) for full API reference and [docs/API_EXAMPLES.md](docs/API_EXAMPLES.md) for examples.

## Configuration

Edit `src/eink_config.json`:

| Setting | Default | Description |
|---------|---------|-------------|
| `refresh_interval` | 360 | Seconds between updates (6 min) |
| `display_width` | 800 | Display width in pixels |
| `display_height` | 480 | Display height in pixels |

## Project Structure

```text
src/                       # Core application
├── api/                   # API endpoints and data fetching
├── display/               # Display controllers
├── services/              # Business logic
├── assets/logos/           # Team and league logos
├── static/                # CSS, JS, static assets
└── test-data/             # Test game data

tests/                     # Test suite (unit, integration, JS)
scripts/                   # Pi installation and setup scripts
docs/                      # Documentation
```

## Development

```bash
make install        # Install all dependencies
make install-hooks  # Install pre-commit hooks
make check          # Run all linters and formatters
make test           # Run all tests (Python + JavaScript)
make test-coverage  # Run with coverage reports
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for full development setup.

## Hardware

- [Raspberry Pi Zero 2 W](https://shop.pimoroni.com/products/raspberry-pi-zero-2-w)
- [Inky Impression 7.3"](https://shop.pimoroni.com/products/inky-impression-7-3?variant=55186435244411) (800x480, 7-color)
