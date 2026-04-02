"""
Configuration API endpoints for reading and writing scoreboard settings.

Provides GET/POST /api/config for the web settings panel.
Reads and writes to both eink_config.json (backend) and config.js (frontend).
"""

import json
import logging
import os
import re
import time

from flask import Blueprint, jsonify, request

from api.auth import login_required, validate_csrf_token

logger = logging.getLogger(__name__)

config_bp = Blueprint("config", __name__)

# Paths relative to project root (src/ directory)
EINK_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "eink_config.json")
JS_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "static", "js", "config.js"
)

# Maps between JS constant references and actual values
TIMEZONE_MAP = {
    "America/New_York": "TIMEZONES.EASTERN",
    "America/Chicago": "TIMEZONES.CENTRAL",
    "America/Denver": "TIMEZONES.MOUNTAIN",
    "America/Los_Angeles": "TIMEZONES.PACIFIC",
    "America/Phoenix": "TIMEZONES.ARIZONA",
    "America/Anchorage": "TIMEZONES.ALASKA",
    "Pacific/Honolulu": "TIMEZONES.HAWAII",
}

TIMEZONE_REVERSE = {v: k for k, v in TIMEZONE_MAP.items()}

THEME_MAP = {
    "default": "THEMES.DEFAULT",
    "team_colors": "THEMES.TEAM_COLORS",
    "mlb_scoreboard": "THEMES.MLB_SCOREBOARD",
}

THEME_REVERSE = {v: k for k, v in THEME_MAP.items()}

SCREENSAVER_MODE_MAP = {
    "off": "SCREENSAVER_MODES.OFF",
    "no_games": "SCREENSAVER_MODES.NO_GAMES",
    "after_last_game": "SCREENSAVER_MODES.AFTER_LAST_GAME",
}

SCREENSAVER_MODE_REVERSE = {v: k for k, v in SCREENSAVER_MODE_MAP.items()}

SCREENSAVER_FEED_TYPES = ["news", "photos", "both"]

# All 30 MLB teams
MLB_TEAMS = [
    "Arizona Diamondbacks",
    "Atlanta Braves",
    "Baltimore Orioles",
    "Boston Red Sox",
    "Chicago Cubs",
    "Chicago White Sox",
    "Cincinnati Reds",
    "Cleveland Guardians",
    "Colorado Rockies",
    "Detroit Tigers",
    "Houston Astros",
    "Kansas City Royals",
    "Los Angeles Angels",
    "Los Angeles Dodgers",
    "Miami Marlins",
    "Milwaukee Brewers",
    "Minnesota Twins",
    "New York Mets",
    "New York Yankees",
    "Athletics",
    "Philadelphia Phillies",
    "Pittsburgh Pirates",
    "San Francisco Giants",
    "Seattle Mariners",
    "St. Louis Cardinals",
    "Tampa Bay Rays",
    "Texas Rangers",
    "Toronto Blue Jays",
    "Washington Nationals",
]


def read_eink_config():
    """Read eink_config.json and return as dict."""
    path = os.path.normpath(EINK_CONFIG_PATH)
    with open(path) as f:
        return json.load(f)


def write_eink_config(config):
    """Write dict to eink_config.json."""
    path = os.path.normpath(EINK_CONFIG_PATH)
    with open(path, "w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")


def read_js_config():
    """Parse config.js and return user-configurable values as a dict.

    Resolves JS constant references (e.g., TIMEZONES.PACIFIC -> America/Los_Angeles).
    """
    path = os.path.normpath(JS_CONFIG_PATH)
    with open(path) as f:
        content = f.read()

    config = {}

    # Parse FEATURE_FLAGS
    flags_match = re.search(r"export const FEATURE_FLAGS\s*=\s*\{([^}]+)\}", content)
    if flags_match:
        flags_block = flags_match.group(1)
        config["show_standings"] = "SHOW_STANDINGS: true" in flags_block
        config["eink_optimized_contrast"] = (
            "EINK_OPTIMIZED_CONTRAST: true" in flags_block
        )
        config["show_screensaver"] = "SHOW_SCREENSAVER: true" in flags_block

    # Parse favoriteTeams
    teams_match = re.search(r"export const favoriteTeams\s*=\s*\{([^}]+)\}", content)
    if teams_match:
        teams_block = teams_match.group(1)
        mlb_match = re.search(r"mlb:\s*(\[.*?\]|null)", teams_block)
        if mlb_match:
            mlb_val = mlb_match.group(1)
            if mlb_val == "null":
                config["favorite_teams"] = []
            else:
                config["favorite_teams"] = re.findall(r"'([^']+)'", mlb_val)
        else:
            config["favorite_teams"] = []

    # Parse displayTimezone
    tz_match = re.search(r"export const displayTimezone\s*=\s*(.+?);", content)
    if tz_match:
        tz_val = tz_match.group(1).strip()
        # Resolve TIMEZONES.X constant or strip quotes from direct string
        if tz_val in TIMEZONE_REVERSE:
            config["timezone"] = TIMEZONE_REVERSE[tz_val]
        else:
            config["timezone"] = tz_val.strip("'\"")

    # Parse currentTheme
    theme_match = re.search(r"export const currentTheme\s*=\s*(.+?);", content)
    if theme_match:
        theme_val = theme_match.group(1).strip()
        if theme_val in THEME_REVERSE:
            config["theme"] = THEME_REVERSE[theme_val]
        else:
            config["theme"] = theme_val.strip("'\"")

    # Parse screensaverMode
    mode_match = re.search(r"export const screensaverMode\s*=\s*(.+?);", content)
    if mode_match:
        mode_val = mode_match.group(1).strip()
        if mode_val in SCREENSAVER_MODE_REVERSE:
            config["screensaver_mode"] = SCREENSAVER_MODE_REVERSE[mode_val]
        else:
            config["screensaver_mode"] = mode_val.strip("'\"")

    return config


def write_js_config(updates):
    """Update specific values in config.js while preserving the rest of the file.

    Accepts resolved values (e.g., "America/Los_Angeles") and converts
    to JS constant references (e.g., TIMEZONES.PACIFIC) when possible.
    """
    path = os.path.normpath(JS_CONFIG_PATH)
    with open(path) as f:
        content = f.read()

    if "favorite_teams" in updates:
        teams = updates["favorite_teams"]
        if teams:
            teams_js = ", ".join(f"'{t}'" for t in teams)
            teams_val = f"[{teams_js}]"
        else:
            teams_val = "null"
        content = re.sub(
            r"(export const favoriteTeams\s*=\s*)\{[^}]+\}",
            rf"\g<1>{{ mlb: {teams_val}, nfl: null, cfb: null }}",
            content,
        )

    if "timezone" in updates:
        tz = updates["timezone"]
        tz_js = TIMEZONE_MAP.get(tz, f"'{tz}'")
        content = re.sub(
            r"(export const displayTimezone\s*=\s*).+?;",
            rf"\g<1>{tz_js};",
            content,
        )

    if "theme" in updates:
        theme = updates["theme"]
        theme_js = THEME_MAP.get(theme, f"'{theme}'")
        content = re.sub(
            r"(export const currentTheme\s*=\s*).+?;",
            rf"\g<1>{theme_js};",
            content,
        )

    if "screensaver_mode" in updates:
        mode = updates["screensaver_mode"]
        mode_js = SCREENSAVER_MODE_MAP.get(mode, f"'{mode}'")
        content = re.sub(
            r"(export const screensaverMode\s*=\s*).+?;",
            rf"\g<1>{mode_js};",
            content,
        )
        # Derive SHOW_SCREENSAVER from screensaver_mode
        updates["show_screensaver"] = mode != "off"

    # Build FEATURE_FLAGS from individual boolean fields
    flag_keys = {
        "show_standings": "SHOW_STANDINGS",
        "eink_optimized_contrast": "EINK_OPTIMIZED_CONTRAST",
        "show_screensaver": "SHOW_SCREENSAVER",
    }
    flag_updates = {
        js_key: updates[py_key]
        for py_key, js_key in flag_keys.items()
        if py_key in updates
    }
    if flag_updates:
        # Read current flags first so we only update what was sent
        current = read_js_config()
        flags = {
            "SHOW_STANDINGS": updates.get(
                "show_standings", current.get("show_standings", False)
            ),
            "EINK_OPTIMIZED_CONTRAST": updates.get(
                "eink_optimized_contrast",
                current.get("eink_optimized_contrast", True),
            ),
            "SHOW_SCREENSAVER": updates.get(
                "show_screensaver", current.get("show_screensaver", True)
            ),
        }
        flags_str = ", ".join(
            f"{k}: {'true' if v else 'false'}" for k, v in flags.items()
        )
        content = re.sub(
            r"(export const FEATURE_FLAGS\s*=\s*)\{[^}]+\}",
            rf"\g<1>{{ {flags_str} }}",
            content,
        )

    with open(path, "w") as f:
        f.write(content)


@config_bp.route("/api/config", methods=["GET"])
def get_config():
    """Return merged configuration from both config files."""
    try:
        eink = read_eink_config()
        js = read_js_config()

        return jsonify(
            {
                "refresh_interval": eink.get("refresh_interval", 360),
                "favorite_teams": js.get("favorite_teams", []),
                "timezone": js.get("timezone", "America/New_York"),
                "theme": js.get("theme", "default"),
                "show_screensaver": js.get("show_screensaver", True),
                "eink_optimized_contrast": js.get("eink_optimized_contrast", True),
                "show_standings": js.get("show_standings", False),
                "screensaver_mode": js.get(
                    "screensaver_mode",
                    eink.get("screensaver_mode", "no_games"),
                ),
                "screensaver_feed_type": eink.get(
                    "screensaver_feed_type", "news"
                ),
                "available_teams": MLB_TEAMS,
                "available_timezones": list(TIMEZONE_MAP.keys()),
                "available_themes": list(THEME_MAP.keys()),
                "available_screensaver_modes": list(
                    SCREENSAVER_MODE_MAP.keys()
                ),
                "available_screensaver_feed_types": SCREENSAVER_FEED_TYPES,
            }
        )
    except Exception as e:
        logger.error(f"Error reading config: {e}")
        return jsonify({"error": str(e)}), 500


@config_bp.route("/api/config", methods=["POST"])
@login_required
def update_config():
    """Update configuration. Accepts partial updates."""
    try:
        if not validate_csrf_token():
            return jsonify({"error": "Invalid CSRF token"}), 403

        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Validate inputs
        errors = validate_config(data)
        if errors:
            return jsonify({"error": "Validation failed", "details": errors}), 400

        # Update eink_config.json
        eink_needs_write = False
        eink = read_eink_config()
        if "refresh_interval" in data:
            eink["refresh_interval"] = int(data["refresh_interval"])
            eink_needs_write = True
        if "screensaver_mode" in data:
            eink["screensaver_mode"] = data["screensaver_mode"]
            eink_needs_write = True
        if "screensaver_feed_type" in data:
            eink["screensaver_feed_type"] = data["screensaver_feed_type"]
            eink_needs_write = True
        if eink_needs_write:
            write_eink_config(eink)

        # Update config.js
        js_updates = {}
        for key in [
            "favorite_teams",
            "timezone",
            "theme",
            "show_screensaver",
            "eink_optimized_contrast",
            "show_standings",
            "screensaver_mode",
        ]:
            if key in data:
                js_updates[key] = data[key]

        if js_updates:
            write_js_config(js_updates)

        logger.info(f"Configuration updated: {list(data.keys())}")

        # Restart display service to pick up new refresh interval
        service_restarted = False
        if "refresh_interval" in data:
            service_restarted = _restart_display_service()

        return jsonify(
            {
                "status": "ok",
                "updated": list(data.keys()),
                "service_restarted": service_restarted,
            }
        )

    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return jsonify({"error": str(e)}), 500


@config_bp.route("/api/config/status", methods=["GET"])
def get_status():
    """Return service status and system information."""
    try:
        status = {
            "server_uptime": _get_server_uptime(),
            "screenshot_age": _get_screenshot_age(),
        }

        # Add systemd service status if available
        services = _get_service_status()
        if services:
            status["services"] = services

        return jsonify(status)

    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({"error": str(e)}), 500


def validate_config(data):
    """Validate configuration values. Returns list of error strings."""
    errors = []

    if "refresh_interval" in data:
        try:
            interval = int(data["refresh_interval"])
            if interval < 60 or interval > 3600:
                errors.append("refresh_interval must be between 60 and 3600 seconds")
        except (ValueError, TypeError):
            errors.append("refresh_interval must be a number")

    if "favorite_teams" in data:
        teams = data["favorite_teams"]
        if not isinstance(teams, list):
            errors.append("favorite_teams must be a list")
        elif teams:
            invalid = [t for t in teams if t not in MLB_TEAMS]
            if invalid:
                errors.append(f"Invalid team names: {invalid}")

    if "timezone" in data:
        tz = data["timezone"]
        if tz not in TIMEZONE_MAP and not isinstance(tz, str):
            errors.append(f"Invalid timezone: {tz}")

    if "theme" in data:
        theme = data["theme"]
        if theme not in THEME_MAP:
            errors.append(
                f"Invalid theme: {theme}. Must be one of: {list(THEME_MAP.keys())}"
            )

    for bool_field in ["show_screensaver", "eink_optimized_contrast", "show_standings"]:
        if bool_field in data and not isinstance(data[bool_field], bool):
            errors.append(f"{bool_field} must be a boolean")

    if "screensaver_mode" in data:
        mode = data["screensaver_mode"]
        if mode not in SCREENSAVER_MODE_MAP:
            errors.append(
                f"Invalid screensaver_mode: {mode}. "
                f"Must be one of: {list(SCREENSAVER_MODE_MAP.keys())}"
            )

    if "screensaver_feed_type" in data:
        feed_type = data["screensaver_feed_type"]
        if feed_type not in SCREENSAVER_FEED_TYPES:
            errors.append(
                f"Invalid screensaver_feed_type: {feed_type}. "
                f"Must be one of: {SCREENSAVER_FEED_TYPES}"
            )

    return errors


# Server start time for uptime calculation
_server_start_time = time.time()


def _get_server_uptime():
    """Return server uptime in seconds."""
    return int(time.time() - _server_start_time)


def _get_screenshot_age():
    """Return age of the latest screenshot in seconds, or None."""
    screenshot_path = "/tmp/sports_display.png"
    try:
        if os.path.exists(screenshot_path):
            return int(time.time() - os.path.getmtime(screenshot_path))
    except OSError:
        pass
    return None


def _get_service_status():
    """Return status of systemd services, or None if not available."""
    try:
        import subprocess

        services = {}
        for svc in ["sports-server", "sports-display", "sports-watchdog"]:
            result = subprocess.run(
                ["/usr/bin/systemctl", "is-active", f"{svc}.service"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            services[svc] = result.stdout.strip()
        return services
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def _restart_display_service():
    """Restart sports-display service to pick up config changes."""
    try:
        import subprocess

        result = subprocess.run(
            [
                "/usr/bin/sudo",
                "/usr/bin/systemctl",
                "restart",
                "sports-display.service",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            logger.info("Display service restarted after config change")
            return True
        else:
            logger.error(f"Failed to restart display service: {result.stderr.strip()}")
            return False
    except Exception as e:
        logger.error(f"Error restarting display service: {e}")
        return False


# Allowed services for restart (whitelist for safety)
_ALLOWED_SERVICES = {"sports-display", "sports-watchdog"}


@config_bp.route("/api/services/status", methods=["GET"])
def get_services_status():
    """Return detailed status of all three systemd services."""
    try:
        import subprocess

        services = {}
        for svc in ["sports-server", "sports-display", "sports-watchdog"]:
            svc_name = f"{svc}.service"
            info = {"status": "unknown"}

            try:
                # Get active state
                result = subprocess.run(
                    ["/usr/bin/systemctl", "is-active", svc_name],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                info["status"] = result.stdout.strip()

                # Get uptime from ActiveEnterTimestamp
                result = subprocess.run(
                    [
                        "/usr/bin/systemctl",
                        "show",
                        svc_name,
                        "--property=ActiveEnterTimestamp",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                timestamp_line = result.stdout.strip()
                if "=" in timestamp_line:
                    info["started_at"] = timestamp_line.split("=", 1)[1].strip()

            except subprocess.TimeoutExpired:
                info["status"] = "timeout"

            services[svc] = info

        # System uptime
        try:
            with open("/proc/uptime") as f:
                system_uptime = int(float(f.read().split()[0]))
        except (FileNotFoundError, ValueError):
            system_uptime = None

        return jsonify(
            {
                "services": services,
                "system_uptime": system_uptime,
                "server_uptime": _get_server_uptime(),
                "screenshot_age": _get_screenshot_age(),
            }
        )

    except FileNotFoundError:
        return jsonify({"error": "systemctl not available"}), 503
    except Exception as e:
        logger.error(f"Error getting service status: {e}")
        return jsonify({"error": str(e)}), 500


@config_bp.route("/api/services/restart", methods=["POST"])
@login_required
def restart_service():
    """Restart a scoreboard service. Requires sudoers rule on Pi."""
    try:
        import subprocess

        data = request.get_json(silent=True) or {}
        service = data.get("service", "sports-display")

        if service not in _ALLOWED_SERVICES:
            return (
                jsonify(
                    {
                        "error": f"Service '{service}' not allowed. "
                        f"Must be one of: {sorted(_ALLOWED_SERVICES)}"
                    }
                ),
                400,
            )

        svc_name = f"{service}.service"
        logger.info(f"Restarting service: {svc_name}")

        result = subprocess.run(
            ["/usr/bin/sudo", "/usr/bin/systemctl", "restart", svc_name],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            return jsonify({"status": "ok", "service": service, "action": "restarted"})
        else:
            error_msg = result.stderr.strip() or "Unknown error"
            logger.error(f"Failed to restart {svc_name}: {error_msg}")
            return jsonify({"error": error_msg, "service": service}), 500

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Restart timed out"}), 504
    except FileNotFoundError:
        return jsonify({"error": "systemctl not available"}), 503
    except Exception as e:
        logger.error(f"Error restarting service: {e}")
        return jsonify({"error": str(e)}), 500
