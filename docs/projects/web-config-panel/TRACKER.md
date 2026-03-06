# Web Configuration Panel -- Tracker

## Phase 1: Config API

Build the backend endpoints for reading and writing configuration.

- [x] Create `src/api/config_api.py` with a Flask Blueprint:
  - [x] `GET /api/config` -- return merged config from `eink_config.json` and `config.js`
  - [x] `POST /api/config` -- validate and write changes to both config files
  - [x] `GET /api/config/status` -- return service health, uptime, last refresh time
- [x] Write a config file parser for `config.js` (extract/update JS variable values)
- [x] Register the config Blueprint in `dev_server.py`
- [x] Add unit tests for config API endpoints (29 tests)
- [x] Add integration tests for config read/write round-trip (9 tests)

## Phase 2: Settings Page

Build the browser-based settings form.

- [x] Create `src/templates/settings.html` (Jinja2 template):
  - [x] Form for favorite MLB teams (multi-select, all 30 teams)
  - [x] Timezone dropdown (match options from `configure.sh`)
  - [x] Theme selector (Default, Team Colors, MLB Scoreboard)
  - [x] Refresh interval control (slider or dropdown)
  - [x] Screensaver toggle (enable/disable)
  - [x] Contrast optimization toggle
- [x] Add `/settings` route to `dev_server.py`
- [x] Add HTMX (`<script>` tag) for inline form submission:
  - [x] `hx-post="/api/config"` on form submit
  - [x] Success/error feedback without full page reload
  - [x] Loading indicator during save
- [x] Style the settings page:
  - [x] Create `src/static/styles/settings.css`
  - [x] Match the look and feel of the existing display page
  - [x] Responsive layout (works on phone, tablet, desktop)
- [x] Add a link/nav element to access settings from the main display page

## Phase 3: Service Management

Let users restart services and view status from the settings page.

- [x] Add service control endpoints:
  - [x] `POST /api/services/restart` -- restart the display service
  - [x] `GET /api/services/status` -- return status of all three services
- [x] Create sudoers rule template (`services/scoreboard-sudoers`):
  - [x] Allow Flask user to run `systemctl restart/status` for scoreboard services
  - [x] No broader sudo access
- [x] Add to `scripts/setup-services.sh`:
  - [x] Install sudoers rule during service setup
- [x] Add service status panel to settings page:
  - [x] Show status of each service (active/inactive/failed)
  - [x] Show last display refresh time
  - [x] Show system uptime
  - [x] Restart button for the display service
- [x] Add HTMX polling for live status updates (`hx-trigger="every 10s"`)
- [x] Add integration tests for service endpoints (9 tests)

## Phase 4: Network Discovery (mDNS)

Make the scoreboard discoverable at `scoreboard.local` on the local network.

- [x] Add to `scripts/install.sh`:
  - [x] Install `avahi-daemon` if not already present
  - [x] Set hostname to `scoreboard` via `hostnamectl`
  - [x] Update `/etc/hosts` with new hostname
  - [x] Enable and start `avahi-daemon` service
- [x] Create Avahi service file (`services/scoreboard-avahi.service`):
  - [x] Advertise HTTP service on port 5001
  - [x] Service name: "E-Ink Scoreboard"
- [x] Update `docs/RASPBERRY_PI_SETUP.md`:
  - [x] Document `scoreboard.local` access
  - [x] Note Windows compatibility requirements (Bonjour/iTunes)
- [ ] Test discovery from macOS, iOS, Windows, Linux

## Phase 5: Security

Add optional authentication to protect config changes.

- [x] Add admin password setup to `scripts/configure.sh`:
  - [x] Generate random password on first install
  - [x] Display password to user during setup
  - [x] Store SHA-256 hash in `src/.admin_password` (gitignored)
  - [x] Option to set custom password
- [x] Add authentication to Flask:
  - [x] Login page at `/login`
  - [x] Session-based auth using Flask sessions
  - [x] `@login_required` decorator on write endpoints
  - [x] Read-only endpoints remain public
  - [x] Session timeout after inactivity (30 min)
- [x] Add CSRF protection:
  - [x] Include CSRF token in settings form and restart requests
  - [x] Validate token on `POST` requests
- [x] Add `.admin_password` and `.flask_secret` to `.gitignore`
- [x] Add unit tests for auth module (10 tests)
- [x] Add integration tests for auth endpoints (16 tests)

## Phase 6: WiFi Management

Web-based WiFi network switching via nmcli.

- [x] Create `src/api/wifi_api.py` with Flask Blueprint:
  - [x] `GET /api/wifi/status` -- current connection and IP address
  - [x] `GET /api/wifi/networks` -- scan and list available networks
  - [x] `POST /api/wifi/connect` -- connect to a network (auth + CSRF protected)
- [x] Add SSID validation (printable ASCII, max 32 chars)
- [x] Add sudoers rule for `nmcli dev wifi connect` in `services/scoreboard-sudoers`
- [x] Register wifi Blueprint in `dev_server.py`
- [x] Add WiFi section to settings page:
  - [x] Show current connection status and IP
  - [x] Scan button with network list (SSID, signal, security)
  - [x] Connect dialog with password input
  - [x] Deduplication of SSIDs in scan results
- [x] Add integration tests for WiFi endpoints (13 tests)

> **Note:** Comitup (captive portal / AP mode) was dropped from scope.
> mDNS discovery + web WiFi controls cover the primary use case.
> AP mode would require testing on Pi Zero 2 W hardware to evaluate
> memory impact and NetworkManager compatibility.
