# E-Ink Sports Scores API Documentation

This document describes the REST API endpoints for the E-Ink Sports Scores project.

## Base URL

When running locally: `http://localhost:5001`

## Authentication

Read endpoints are public. Write endpoints (`POST /api/config`, `POST /api/services/restart`,
`POST /api/wifi/connect`) require authentication when an admin password is configured.

Authentication is optional. When `src/.admin_password` exists, write endpoints and the
`/settings` page require login via `/login`. CSRF tokens are required on all POST requests
when auth is enabled (sent via `X-CSRF-Token` header).

## Content Types

All responses return `application/json` unless otherwise specified.

---

## Endpoints Overview

| Endpoint                    | Method | Description                              |
| --------------------------- | ------ | ---------------------------------------- |
| `/api/scores/MLB`           | GET    | Fetch live MLB game scores and standings |
| `/api/scores/NFL`           | GET    | Fetch live NFL game scores               |
| `/api/screensaver/<league>` | GET    | Fetch team news article for screensaver  |
| `/api/config`               | GET    | Read current scoreboard configuration    |
| `/api/config`               | POST   | Update scoreboard configuration          |
| `/api/config/status`        | GET    | Server uptime and screenshot age         |
| `/api/services/status`      | GET    | Status of all systemd services           |
| `/api/services/restart`     | POST   | Restart a scoreboard service             |
| `/api/wifi/status`          | GET    | Current WiFi connection info             |
| `/api/wifi/networks`        | GET    | Scan available WiFi networks             |
| `/api/wifi/connect`         | POST   | Connect to a WiFi network                |
| `/settings`                 | GET    | Web configuration panel                  |
| `/login`                    | GET    | Admin login page (when auth enabled)     |
| `/display`                  | GET    | HTML display page for e-ink rendering    |
| `/check-updates`            | GET    | Development endpoint for hot reload      |

---

## Sports Scores API

### MLB Scores

**Endpoint:** `GET /api/scores/MLB`

**Description:** Fetches live MLB game data including scores, standings, and game status for today. If no games today, returns yesterday's completed games.

#### MLB Response Format

```json
[
  {
    "away_team": "New York Yankees",
    "home_team": "Boston Red Sox",
    "away_score": 7,
    "home_score": 4,
    "away_record": "82-65",
    "home_record": "78-69",
    "status": "Final",
    "venue": "Fenway Park",
    "bases": {
      "first": false,
      "second": true,
      "third": false
    },
    "outs": 2
  }
]
```

#### MLB Field Descriptions

| Field         | Type           | Description             | Notes                       |
| ------------- | -------------- | ----------------------- | --------------------------- |
| `away_team`   | string         | Visiting team full name | e.g., "New York Yankees"    |
| `home_team`   | string         | Home team full name     | e.g., "Boston Red Sox"      |
| `away_score`  | integer        | Away team score         | 0 if game not started       |
| `home_score`  | integer        | Home team score         | 0 if game not started       |
| `away_record` | string         | Away team season record | Format: "wins-losses"       |
| `home_record` | string         | Home team season record | Format: "wins-losses"       |
| `status`      | string         | Current game status     | See status values below     |
| `venue`       | string or null | Stadium name            | null if unavailable         |
| `bases`       | object         | Base runner positions   | Only present for live games |
| `outs`        | integer        | Current number of outs  | Only present for live games |

#### Status Values

| Status          | Description                         |
| --------------- | ----------------------------------- |
| `"Final"`       | Game completed                      |
| `"Top 9th"`     | Live game, top of 9th inning        |
| `"Bot 3rd"`     | Live game, bottom of 3rd inning     |
| `"7:30 PM ET"`  | Scheduled game start time           |
| `"In Progress"` | Live game, no inning info available |

#### MLB Error Response

```json
{
  "error": "Error message description"
}
```

### NFL Scores

**Endpoint:** `GET /api/scores/NFL`

**Description:** Fetches live NFL game data for the current week, limited to 6 games.

#### NFL Response Format

```json
[
  {
    "away_team": "Kansas City Chiefs",
    "home_team": "Buffalo Bills",
    "away_score": 21,
    "home_score": 14,
    "status": "Q3 8:42"
  }
]
```

#### NFL Field Descriptions

| Field        | Type    | Description                     |
| ------------ | ------- | ------------------------------- |
| `away_team`  | string  | Visiting team full display name |
| `home_team`  | string  | Home team full display name     |
| `away_score` | integer | Away team score                 |
| `home_score` | integer | Home team score                 |
| `status`     | string  | Game status or time             |

#### NFL Status Values

| Status         | Description                |
| -------------- | -------------------------- |
| `"Final"`      | Game completed             |
| `"Q1 14:32"`   | Quarter 1, 14:32 remaining |
| `"Q4 2:15"`    | Quarter 4, 2:15 remaining  |
| `"1:00 PM ET"` | Scheduled game time        |

---

## Screensaver API

### Team News Article

**Endpoint:** `GET /api/screensaver/<league>`

**Parameters:**

- `league` (path): League identifier (`MLB`, `NFL`, etc.)

**Description:** Fetches a random recent news article for the user's configured favorite team in the specified league.

#### Screensaver Response Format

```json
{
  "title": "Mariners Sign New Pitcher for Playoff Push",
  "description": "The Seattle Mariners announced today they have signed veteran pitcher...",
  "published": "September 8, 2025",
  "image_url": "https://example.com/article-image-800x480.jpg",
  "link": "https://example.com/full-article",
  "team": "Seattle Mariners",
  "type": "screensaver"
}
```

#### Screensaver Field Descriptions

| Field         | Type           | Description                                 |
| ------------- | -------------- | ------------------------------------------- |
| `title`       | string         | Article headline                            |
| `description` | string         | Article summary, max 200 characters         |
| `published`   | string         | Publication date in "Month DD, YYYY" format |
| `image_url`   | string or null | Article image URL, optimized for 800x480    |
| `link`        | string         | URL to full article                         |
| `team`        | string         | Team name the article is about              |
| `type`        | string         | Always "screensaver"                        |

#### Screensaver Error Response

```json
{
  "error": "No RSS feed configured for favorite teams",
  "title": "Unable to load news",
  "description": "News content is temporarily unavailable.",
  "published": "September 8, 2025",
  "image_url": null,
  "type": "screensaver"
}
```

---

## Display Endpoints

### Main Display Page

**Endpoint:** `GET /display`

**Description:** Returns the HTML page optimized for e-ink display rendering (800x480px).

**Query Parameters:**

- `test=true` - Load sample/test data instead of live data
- `screensaver=true` - Force screensaver mode regardless of game availability

#### Response

Returns HTML content optimized for e-ink displays with inline styles and JavaScript modules.

**Content-Type:** `text/html`

### Development Endpoints

#### Hot Reload Check

**Endpoint:** `GET /check-updates`

**Description:** Development endpoint that checks if source files have been modified for hot reload functionality.

#### Hot Reload Response Format

```json
{
  "changed": true
}
```

---

## Configuration API

### Read Configuration

**Endpoint:** `GET /api/config`

**Description:** Returns the merged configuration from both `eink_config.json` and `config.js`, plus available options for teams, timezones, and themes.

```json
{
  "refresh_interval": 360,
  "favorite_teams": ["Seattle Mariners"],
  "timezone": "America/Los_Angeles",
  "theme": "default",
  "show_screensaver": true,
  "eink_optimized_contrast": true,
  "available_teams": ["Arizona Diamondbacks", "..."],
  "available_timezones": ["America/New_York", "..."],
  "available_themes": ["default", "team_colors", "mlb_scoreboard"]
}
```

### Update Configuration

**Endpoint:** `POST /api/config`

**Description:** Accepts partial updates. Writes to `eink_config.json` and/or `config.js` as appropriate. Requires authentication when enabled.

**Request Body:**

```json
{
  "favorite_teams": ["Seattle Mariners", "New York Yankees"],
  "timezone": "America/New_York",
  "theme": "team_colors",
  "refresh_interval": 900,
  "show_screensaver": false
}
```

### System Status

**Endpoint:** `GET /api/config/status`

**Description:** Returns server uptime and screenshot age.

```json
{
  "server_uptime": 3600,
  "screenshot_age": 120,
  "services": {
    "sports-server": "active",
    "sports-display": "active",
    "sports-watchdog": "active"
  }
}
```

---

## Service Management API

### Service Status

**Endpoint:** `GET /api/services/status`

**Description:** Returns detailed status of all three systemd services.

### Restart Service

**Endpoint:** `POST /api/services/restart`

**Description:** Restarts an allowed scoreboard service. Only `sports-display` and `sports-watchdog` can be restarted (whitelisted). Requires authentication when enabled.

**Request Body:**

```json
{
  "service": "sports-display"
}
```

---

## WiFi Management API

### WiFi Status

**Endpoint:** `GET /api/wifi/status`

**Description:** Returns current WiFi connection info. Returns 503 if `nmcli` is not available.

```json
{
  "connected": true,
  "network": "HomeWifi",
  "device": "wlan0",
  "ip_address": "192.168.1.100"
}
```

### Scan Networks

**Endpoint:** `GET /api/wifi/networks`

**Description:** Triggers a WiFi rescan and returns available networks sorted by signal strength.

```json
{
  "networks": [
    {
      "ssid": "HomeWifi",
      "signal": 85,
      "security": "WPA2",
      "active": true
    }
  ]
}
```

### Connect to Network

**Endpoint:** `POST /api/wifi/connect`

**Description:** Connects to a WiFi network. Requires authentication when enabled.

**Request Body:**

```json
{
  "ssid": "NetworkName",
  "password": "wifi-password"
}
```

---

## Data Sources

### MLB Data

- **Primary:** MLB Stats API (`https://statsapi.mlb.com/api/v1`)
- **Endpoints Used:**
  - `/schedule/games/` - Game schedules and scores
  - `/standings` - Team standings and records

### NFL Data

- **Primary:** ESPN NFL API (`https://site.api.espn.com/apis/site/v2/sports/football/nfl`)
- **Endpoints Used:**
  - `/scoreboard` - Live scores and game status

### Team News

- **Source:** RSS feeds configured in `config/team-rss-feeds.json`
- **Parser:** Python `feedparser` library
- **Selection:** Random article from 10 most recent entries

---

## Rate Limits

No rate limits are enforced by this API, but please note:

- **MLB API:** Subject to MLB's rate limiting
- **ESPN API:** Subject to ESPN's rate limiting
- **RSS Feeds:** Respect individual feed publisher limits

---

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK` - Successful request
- `400 Bad Request` - Invalid parameters
- `404 Not Found` - Endpoint not found
- `500 Internal Server Error` - Server error

Error responses include descriptive error messages in JSON format.

---

## Development Configuration

### Favorite Teams

Configure favorite teams in `src/static/js/config.js`:

```javascript
const favoriteTeams = {
  mlb: ['Seattle Mariners'],
  nfl: null,
};
```

### RSS Feed Configuration

Team RSS feeds are configured in `config/team-rss-feeds.json`.
