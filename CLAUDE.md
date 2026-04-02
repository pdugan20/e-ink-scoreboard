# E-Ink Scoreboard

Real-time MLB scores on a Pimoroni Inky e-ink display. Python/Flask backend
with JavaScript frontend, designed for Raspberry Pi Zero 2 W.

## Common Commands

```bash
# Development
source venv/bin/activate
python src/dev_server.py --port 5001       # Start web server
python src/eink_display.py --once          # Single display update
python src/eink_display.py --once --force  # Force update (bypass game check)

# Testing
make test              # Run all tests (Python + JavaScript)
make test-python       # Python tests only
make test-js           # JavaScript tests only
make test-fast         # Skip slow/e2e tests
make test-coverage     # Run with coverage reports

# Code Quality
make check             # Run all linters and formatters
make lint              # Run linters via pre-commit
make format            # Auto-format all code
make install-hooks     # Install pre-commit hooks

# Setup
make install           # Install all dependencies (Python + Node)
make clean             # Remove cache files
```

## Project Structure

```text
src/
├── api/                    # Flask API endpoints
│   ├── auth.py             # Optional admin auth (login, sessions, CSRF)
│   ├── config_api.py       # /api/config - settings read/write
│   ├── wifi_api.py         # /api/wifi - network scanning/connecting
│   ├── scores_api.py       # /api/scores/MLB - live game scores
│   ├── screensaver_api.py  # /api/screensaver/MLB - team news
│   └── static_files.py     # Static file serving
├── display/                # E-ink display controllers
│   ├── game_checker.py     # Checks for active games
│   ├── refresh_controller.py # Update scheduling logic
│   ├── screenshot_controller.py # Playwright screenshot capture
│   ├── screenshot_worker.py # Screenshot capture subprocess
│   ├── display_worker.py   # E-ink display update subprocess
│   ├── subprocess_guardian.py # Subprocess lifecycle management
│   └── browser_cleanup.py  # Browser process cleanup
├── templates/              # Jinja2 templates
│   ├── settings.html       # Web settings page (HTMX)
│   └── login.html          # Admin login page
├── services/               # Business logic
│   └── screensaver_service.py # News/photos article fetching
├── config/                 # Configuration
│   ├── game_status.py      # Shared game status helpers
│   └── team-rss-feeds.json # RSS feed URLs by team (news + photos)
├── utils/                  # Shared utilities
├── assets/logos/           # Team and league logos
├── static/                 # CSS, JS, static assets
│   ├── js/constants/       # Team data and constants
│   └── styles/             # CSS stylesheets
├── dev_server.py           # Flask development server
├── eink_display.py         # Main display entry point
├── watchdog_monitor.py     # Process health monitoring
└── eink_config.json        # Runtime configuration

tests/
├── unit/                   # Unit tests (API, display logic)
├── integration/            # Integration tests (Flask endpoints)
└── js/                     # JavaScript tests (Vitest)

scripts/                    # Raspberry Pi setup scripts
services/                   # Systemd service and config templates
```

## Architecture

- **Backend**: Flask web server serving scores API, config API, and HTML pages
- **Frontend**: Vanilla JavaScript rendering game cards on an HTML page
- **Settings**: Web config panel at `/settings` using Jinja2 + HTMX (no build step)
- **Display**: Playwright captures screenshots of the HTML page, sends to e-ink display
- **Data**: MLB scores fetched from external API, rendered as game cards in a 3x5 grid
- **Screensaver**: Shows team news articles or AP photos when no games active. Supports multiple feed sources per team (news + photos) with automatic fallback. Can trigger on no-game days or after the last game goes final.
- **Discovery**: Avahi/mDNS advertises `scoreboard.local` on the local network

## Code Style

- **Python**: Black (88 char, py311 target), Ruff (linter), double quotes
- **JavaScript**: Prettier, ESLint, ES modules
- **Markdown**: markdownlint
- Pre-commit hooks enforce all formatting rules

## Testing

- **Python tests**: pytest with `conftest.py` fixtures
- **JavaScript tests**: Vitest with jsdom
- **Integration tests**: marked with `@pytest.mark.integration`, require Playwright
- **Test data**: `src/test-data/` contains sample game data

## Key Patterns

- Display updates use intelligent scheduling: skip updates when no games active
- Mac development uses `requirements-dev.txt` (excludes Pi hardware packages)
- Raspberry Pi uses `requirements.txt` (includes `inky`, `spidev`, `gpiod`)
- Configuration lives in two files: `src/eink_config.json` (backend) and `src/static/js/config.js` (frontend)
- Web settings panel reads/writes both config files via `/api/config`
- Authentication is optional: when `src/.admin_password` exists, write endpoints require login
- Screensaver config split: `screensaver_mode` lives in both config files (frontend needs it for trigger logic), `screensaver_feed_type` lives in `eink_config.json` only (backend-only)
- Scores API returns wrapped response `{ games: [...], all_games_final: bool }` — game status helpers in `src/config/game_status.py` are shared between web API and display controller
- RSS feed config (`team-rss-feeds.json`) uses nested format: `{ "team": { "news": "url", "photos": "url" } }`
