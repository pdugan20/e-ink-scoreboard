# E-Ink Scoreboard

[![CI](https://github.com/pdugan20/e-ink-scoreboard/workflows/CI/badge.svg)](https://github.com/pdugan20/e-ink-scoreboard/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?logo=opensourceinitiative&logoColor=white)](https://opensource.org/licenses/MIT)

Real-time MLB scores on a Pimoroni Inky e-ink display with auto-refresh
and team news screensaver.

Up to 15 games render in a 3x5 grid on an 800x480 display, with on-base
and out indicators on each card. Configure teams, timezone, theme, refresh
interval, and WiFi from a web panel at `scoreboard.local:5001` — no SSH
required.

## Hardware

- [Raspberry Pi Zero 2 W](https://shop.pimoroni.com/products/raspberry-pi-zero-2-w) -
  Must be the Zero 2 W (with WiFi). The original Zero is too slow.
- [Inky Impression 7.3"](https://shop.pimoroni.com/products/inky-impression-7-3?variant=55186435244411) -
  800x480, 7-color e-ink display. Connects directly to the GPIO header.
- [MicroSD Card](https://www.amazon.com/s?k=microSDHC) -
  16GB minimum, Class 10 or better
- [Micro USB Power Supply](https://www.raspberrypi.com/products/micro-usb-power-supply/) -
  5V 2.5A minimum

## Setup

The [Raspberry Pi Setup Guide](docs/RASPBERRY_PI_SETUP.md) walks through
everything from flashing the SD card to a working scoreboard.

If you already have a booted Pi with SSH access:

```bash
sudo apt update && sudo apt install -y git
git clone https://github.com/pdugan20/e-ink-scoreboard.git
cd e-ink-scoreboard
./scripts/setup.sh    # Install, configure, and enable services
sudo reboot           # Apply hardware changes, scoreboard starts automatically
```

After reboot, the scoreboard is accessible at `http://scoreboard.local:5001`.

## Configuration

Open `http://scoreboard.local:5001/settings` from any browser on your network
to configure teams, timezone, theme, refresh interval, WiFi, and more.

All settings changes take effect on the next display refresh. No SSH required.

## Documentation

| Guide                                            | Description                                       |
| ------------------------------------------------ | ------------------------------------------------- |
| [Raspberry Pi Setup](docs/RASPBERRY_PI_SETUP.md) | Complete setup from SD card to working scoreboard |
| [Troubleshooting](docs/TROUBLESHOOTING.md)       | Common issues and solutions                       |
| [Services](docs/SERVICES.md)                     | Systemd service architecture and management       |
| [API Reference](docs/API.md)                     | Full API endpoint documentation                   |
| [API Examples](docs/API_EXAMPLES.md)             | Curl examples and sample responses                |

## Contributing

### Development Environment

Clone the repo and set up a local dev environment on Mac:

```bash
git clone https://github.com/pdugan20/e-ink-scoreboard.git
cd e-ink-scoreboard
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
playwright install chromium
```

Start the dev server and preview the display:

```bash
python src/dev_server.py --port 5001    # Start web server
python src/eink_display.py --once       # Take screenshot (in another terminal)
```

- Live data: <http://localhost:5001/display>
- Test data: <http://localhost:5001/display?test=true>

### Code Quality

```bash
make install-hooks  # Install pre-commit hooks
make check          # Run all linters and formatters
make test           # Run all tests (Python + JavaScript)
make test-coverage  # Run with coverage reports
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for code style, testing conventions, and
CI requirements.

### Project Structure

```text
src/                       # Core application
├── api/                   # API endpoints and data fetching
├── display/               # Display controllers
├── services/              # Business logic
├── assets/logos/          # Team and league logos
├── static/                # CSS, JS, static assets
└── test-data/             # Test game data

tests/                     # Test suite (unit, integration, JS)
scripts/                   # Pi installation and setup scripts
docs/                      # Documentation
```

### Additional Developer Docs

| Guide                                                | Description                                   |
| ---------------------------------------------------- | --------------------------------------------- |
| [Testing](docs/TESTING.md)                           | Test patterns, conventions, and running tests |
| [Logging Style Guide](docs/LOGGING_STYLE_GUIDE.md)   | Log message formatting conventions            |
| [Timeout Architecture](docs/TIMEOUT_ARCHITECTURE.md) | Screenshot timeout strategy deep-dive         |
