# Web Configuration Panel

A browser-based settings page so users can configure their e-ink scoreboard
from any device on the local network without SSH access.

## Background

After initial setup, users must SSH into their Raspberry Pi and re-run
`scripts/configure.sh` to change any settings (favorite teams, timezone,
theme, refresh interval). This is a barrier for non-technical users and
unnecessary friction for everyone else.

The project already runs a Flask web server (`dev_server.py`) on port 5001
that serves the display page and scores API. We extend this server with a
`/settings` page and config API endpoints.

## Architecture Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Backend framework | Flask (existing) | Already running; no new process on 512MB Pi Zero 2 W |
| Frontend interactivity | HTMX | 14KB script tag, no build step, aligns with vanilla JS approach |
| Templating | Jinja2 | Ships with Flask, no additional dependency |
| Database | None | Two config files with ~10 values each; JSON is sufficient |
| New Python dependencies | None | Flask + Jinja2 handle everything |
| Authentication | Session-based, optional | Simple password for write ops, no database needed |
| Discovery | Avahi/mDNS | `scoreboard.local` works on macOS/iOS/Linux out of the box |

## Reference Projects

These production projects run admin panels on Raspberry Pi:

- **Pi-hole** -- Embedded web server, single process, REST API, Basic/Expert
  modes. V6 eliminated external web server dependency entirely.
- **OctoPrint** -- Flask-based admin panel with API keys, plugin system, and
  REST API mirroring the web interface.
- **Home Assistant** -- Python backend, mDNS discovery at
  `homeassistant.local:8123`, emphasizes local control.

## User Flow

1. User opens `http://scoreboard.local:5001/settings` in any browser
2. Settings page shows current configuration with form controls
3. User changes favorite teams, timezone, theme, or refresh interval
4. Form submits via HTMX to `POST /api/config`
5. Flask writes changes to `eink_config.json` and `config.js`
6. Display updates on next refresh cycle (or user clicks "Restart Display")

## Key Files

| File | Role |
|---|---|
| `src/dev_server.py` | Flask app with `/settings` route and blueprint registration |
| `src/api/config_api.py` | Config read/write API and service management endpoints |
| `src/api/auth.py` | Optional admin authentication (sessions, CSRF) |
| `src/api/wifi_api.py` | WiFi scanning and connection via nmcli |
| `src/templates/settings.html` | Settings page (Jinja2 + HTMX) |
| `src/templates/login.html` | Admin login page |
| `src/static/styles/settings.css` | Settings page styles |
| `src/eink_config.json` | Backend config (refresh interval, display settings) |
| `src/static/js/config.js` | Frontend config (teams, timezone, theme) |
| `services/scoreboard-sudoers` | Passwordless systemctl/nmcli rules for web panel |
| `services/scoreboard-avahi.service` | mDNS service advertisement (port 5001) |
| `scripts/configure.sh` | CLI config script (kept as fallback) |

## Config Values to Expose

From `eink_config.json`:

- `refresh_interval` -- how often the display updates (seconds)

From `config.js`:

- `FAVORITE_TEAMS` -- which MLB teams to highlight
- `TIMEZONE` -- display timezone
- `THEME` -- display theme (Default, Team Colors, MLB Scoreboard)
- `SHOW_SCREENSAVER` -- enable/disable team news screensaver
- `EINK_OPTIMIZED_CONTRAST` -- contrast optimization toggle

## Tracker

See [TRACKER.md](TRACKER.md) for the phased task list.
