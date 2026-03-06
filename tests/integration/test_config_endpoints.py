"""
Integration tests for the configuration API endpoints.

Tests the full request/response cycle through the Flask app.
"""

import json
import os
import sys
from unittest.mock import patch

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))

from api import config_api  # noqa: E402
from dev_server import app  # noqa: E402

SAMPLE_JS_CONFIG = """\
// Configuration and feature flags

// Feature flags
export const FEATURE_FLAGS = {
  SHOW_STANDINGS: false,
  EINK_OPTIMIZED_CONTRAST: true,
  SHOW_SCREENSAVER: true,
};

// Favorite team configuration
export const favoriteTeams = {
  mlb: ['Seattle Mariners'],
  nfl: null,
  cfb: null,
};

// Timezone constants
export const TIMEZONES = {
  EASTERN: 'America/New_York',
  CENTRAL: 'America/Chicago',
  MOUNTAIN: 'America/Denver',
  PACIFIC: 'America/Los_Angeles',
  ARIZONA: 'America/Phoenix',
  ALASKA: 'America/Anchorage',
  HAWAII: 'Pacific/Honolulu',
};

// Timezone configuration
export const displayTimezone = TIMEZONES.PACIFIC;

// Theme constants
export const THEMES = {
  DEFAULT: 'default',
  TEAM_COLORS: 'team_colors',
  MLB_SCOREBOARD: 'mlb_scoreboard',
};

// Theme configuration
export const currentTheme = THEMES.DEFAULT;
"""

SAMPLE_EINK_CONFIG = {
    "web_server_url": "http://localhost:5001/display",
    "refresh_interval": 360,
    "display_width": 800,
    "display_height": 480,
}


@pytest.fixture
def client(tmp_path):
    """Create a Flask test client with temporary config files."""
    js_path = tmp_path / "config.js"
    js_path.write_text(SAMPLE_JS_CONFIG)
    eink_path = tmp_path / "eink_config.json"
    eink_path.write_text(json.dumps(SAMPLE_EINK_CONFIG, indent=2))

    original_js = config_api.JS_CONFIG_PATH
    original_eink = config_api.EINK_CONFIG_PATH
    config_api.JS_CONFIG_PATH = str(js_path)
    config_api.EINK_CONFIG_PATH = str(eink_path)

    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

    config_api.JS_CONFIG_PATH = original_js
    config_api.EINK_CONFIG_PATH = original_eink


@pytest.mark.integration
class TestGetConfig:
    """Integration tests for GET /api/config"""

    def test_returns_merged_config(self, client):
        response = client.get("/api/config")
        assert response.status_code == 200
        data = response.get_json()

        assert data["refresh_interval"] == 360
        assert data["favorite_teams"] == ["Seattle Mariners"]
        assert data["timezone"] == "America/Los_Angeles"
        assert data["theme"] == "default"
        assert data["show_screensaver"] is True

    def test_includes_available_options(self, client):
        response = client.get("/api/config")
        data = response.get_json()

        assert "available_teams" in data
        assert len(data["available_teams"]) == 29
        assert "Seattle Mariners" in data["available_teams"]
        assert "available_timezones" in data
        assert "available_themes" in data


@pytest.mark.integration
class TestPostConfig:
    """Integration tests for POST /api/config"""

    def test_updates_single_field(self, client):
        response = client.post(
            "/api/config",
            json={"theme": "team_colors"},
            content_type="application/json",
        )
        assert response.status_code == 200

        # Verify it persisted
        get_response = client.get("/api/config")
        data = get_response.get_json()
        assert data["theme"] == "team_colors"

    def test_updates_multiple_fields(self, client):
        response = client.post(
            "/api/config",
            json={
                "timezone": "America/New_York",
                "refresh_interval": 900,
                "show_screensaver": False,
            },
            content_type="application/json",
        )
        assert response.status_code == 200

        data = client.get("/api/config").get_json()
        assert data["timezone"] == "America/New_York"
        assert data["refresh_interval"] == 900
        assert data["show_screensaver"] is False

    def test_rejects_invalid_data(self, client):
        response = client.post(
            "/api/config",
            json={"refresh_interval": 5},
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_rejects_invalid_team(self, client):
        response = client.post(
            "/api/config",
            json={"favorite_teams": ["Fake Team"]},
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_rejects_empty_body(self, client):
        response = client.post(
            "/api/config",
            data="",
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_preserves_unmodified_fields(self, client):
        # Change only the theme
        client.post(
            "/api/config",
            json={"theme": "mlb_scoreboard"},
            content_type="application/json",
        )

        # Other fields should be unchanged
        data = client.get("/api/config").get_json()
        assert data["theme"] == "mlb_scoreboard"
        assert data["favorite_teams"] == ["Seattle Mariners"]
        assert data["timezone"] == "America/Los_Angeles"
        assert data["refresh_interval"] == 360


@pytest.mark.integration
class TestGetStatus:
    """Integration tests for GET /api/config/status"""

    def test_returns_status(self, client):
        response = client.get("/api/config/status")
        assert response.status_code == 200
        data = response.get_json()

        assert "server_uptime" in data
        assert isinstance(data["server_uptime"], int)
        assert "screenshot_age" in data


@pytest.mark.integration
class TestGetServicesStatus:
    """Integration tests for GET /api/services/status"""

    @patch("api.config_api._get_screenshot_age", return_value=120)
    def test_returns_services_when_systemctl_available(self, mock_age, client):
        mock_result = type("Result", (), {"stdout": "active\n", "returncode": 0})()
        mock_show = type(
            "Result",
            (),
            {
                "stdout": "ActiveEnterTimestamp=Mon 2025-01-01 12:00:00 UTC",
                "returncode": 0,
            },
        )()

        def fake_run(cmd, **kwargs):
            if "is-active" in cmd:
                return mock_result
            if "show" in cmd:
                return mock_show
            return mock_result

        with patch("subprocess.run", side_effect=fake_run):
            response = client.get("/api/services/status")

        assert response.status_code == 200
        data = response.get_json()
        assert "services" in data
        assert "sports-server" in data["services"]
        assert data["services"]["sports-server"]["status"] == "active"
        assert "server_uptime" in data
        assert "screenshot_age" in data

    def test_returns_503_when_systemctl_missing(self, client):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            response = client.get("/api/services/status")
        assert response.status_code == 503


@pytest.mark.integration
class TestRestartService:
    """Integration tests for POST /api/services/restart"""

    def test_restart_allowed_service(self, client):
        mock_result = type(
            "Result", (), {"stdout": "", "stderr": "", "returncode": 0}
        )()
        with patch("subprocess.run", return_value=mock_result):
            response = client.post(
                "/api/services/restart",
                json={"service": "sports-display"},
                content_type="application/json",
            )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
        assert data["service"] == "sports-display"

    def test_restart_watchdog_service(self, client):
        mock_result = type(
            "Result", (), {"stdout": "", "stderr": "", "returncode": 0}
        )()
        with patch("subprocess.run", return_value=mock_result):
            response = client.post(
                "/api/services/restart",
                json={"service": "sports-watchdog"},
                content_type="application/json",
            )
        assert response.status_code == 200

    def test_rejects_disallowed_service(self, client):
        response = client.post(
            "/api/services/restart",
            json={"service": "sports-server"},
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "not allowed" in data["error"]

    def test_rejects_arbitrary_service(self, client):
        response = client.post(
            "/api/services/restart",
            json={"service": "sshd"},
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_handles_restart_failure(self, client):
        mock_result = type(
            "Result", (), {"stdout": "", "stderr": "Failed to restart", "returncode": 1}
        )()
        with patch("subprocess.run", return_value=mock_result):
            response = client.post(
                "/api/services/restart",
                json={"service": "sports-display"},
                content_type="application/json",
            )
        assert response.status_code == 500
        data = response.get_json()
        assert "Failed to restart" in data["error"]

    def test_handles_timeout(self, client):
        import subprocess

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 30)):
            response = client.post(
                "/api/services/restart",
                json={"service": "sports-display"},
                content_type="application/json",
            )
        assert response.status_code == 504

    def test_defaults_to_display_service(self, client):
        mock_result = type(
            "Result", (), {"stdout": "", "stderr": "", "returncode": 0}
        )()
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            response = client.post(
                "/api/services/restart",
                json={},
                content_type="application/json",
            )
        assert response.status_code == 200
        mock_run.assert_called_once()
        assert "sports-display.service" in mock_run.call_args[0][0]
