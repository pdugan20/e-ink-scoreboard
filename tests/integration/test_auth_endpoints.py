"""
Integration tests for authentication endpoints.

Tests login, logout, session management, and protected routes.
"""

import json
import os
import sys

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))

from api import auth, config_api  # noqa: E402
from dev_server import app  # noqa: E402

SAMPLE_JS_CONFIG = """\
export const FEATURE_FLAGS = { SHOW_STANDINGS: false, EINK_OPTIMIZED_CONTRAST: true, SHOW_SCREENSAVER: true };
export const favoriteTeams = { mlb: ['Seattle Mariners'], nfl: null, cfb: null };
export const TIMEZONES = { EASTERN: 'America/New_York', PACIFIC: 'America/Los_Angeles' };
export const displayTimezone = TIMEZONES.PACIFIC;
export const THEMES = { DEFAULT: 'default', TEAM_COLORS: 'team_colors', MLB_SCOREBOARD: 'mlb_scoreboard' };
export const currentTheme = THEMES.DEFAULT;
"""

SAMPLE_EINK_CONFIG = {
    "refresh_interval": 360,
    "display_width": 800,
    "display_height": 480,
}


@pytest.fixture
def auth_client(tmp_path):
    """Create a Flask test client with auth enabled."""
    # Set up config files
    js_path = tmp_path / "config.js"
    js_path.write_text(SAMPLE_JS_CONFIG)
    eink_path = tmp_path / "eink_config.json"
    eink_path.write_text(json.dumps(SAMPLE_EINK_CONFIG))

    # Set up password file
    pw_path = tmp_path / ".admin_password"
    pw_path.write_text(auth._hash_password("testpass123"))

    original_js = config_api.JS_CONFIG_PATH
    original_eink = config_api.EINK_CONFIG_PATH
    original_pw = auth.PASSWORD_FILE

    config_api.JS_CONFIG_PATH = str(js_path)
    config_api.EINK_CONFIG_PATH = str(eink_path)
    auth.PASSWORD_FILE = str(pw_path)

    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"
    with app.test_client() as client:
        yield client

    config_api.JS_CONFIG_PATH = original_js
    config_api.EINK_CONFIG_PATH = original_eink
    auth.PASSWORD_FILE = original_pw


@pytest.fixture
def noauth_client(tmp_path):
    """Create a Flask test client with auth disabled (no password file)."""
    js_path = tmp_path / "config.js"
    js_path.write_text(SAMPLE_JS_CONFIG)
    eink_path = tmp_path / "eink_config.json"
    eink_path.write_text(json.dumps(SAMPLE_EINK_CONFIG))

    original_js = config_api.JS_CONFIG_PATH
    original_eink = config_api.EINK_CONFIG_PATH
    original_pw = auth.PASSWORD_FILE

    config_api.JS_CONFIG_PATH = str(js_path)
    config_api.EINK_CONFIG_PATH = str(eink_path)
    auth.PASSWORD_FILE = str(tmp_path / "nonexistent")

    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"
    with app.test_client() as client:
        yield client

    config_api.JS_CONFIG_PATH = original_js
    config_api.EINK_CONFIG_PATH = original_eink
    auth.PASSWORD_FILE = original_pw


def _login(client, password="testpass123"):
    """Helper to login and return the response."""
    return client.post("/login", data={"password": password, "next": "/settings"})


@pytest.mark.integration
class TestLoginPage:
    """Tests for the login page."""

    def test_login_page_renders(self, auth_client):
        response = auth_client.get("/login")
        assert response.status_code == 200
        assert b"Admin Login" in response.data

    def test_login_redirects_when_auth_disabled(self, noauth_client):
        response = noauth_client.get("/login")
        assert response.status_code == 302
        assert "/settings" in response.headers["Location"]

    def test_successful_login(self, auth_client):
        response = _login(auth_client, "testpass123")
        assert response.status_code == 302

    def test_failed_login(self, auth_client):
        response = _login(auth_client, "wrongpassword")
        assert response.status_code == 401
        assert b"Incorrect password" in response.data

    def test_logout_clears_session(self, auth_client):
        _login(auth_client)
        response = auth_client.get("/logout")
        assert response.status_code == 302

        # Settings should redirect to login now
        response = auth_client.get("/settings")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]


@pytest.mark.integration
class TestProtectedRoutes:
    """Tests for routes that require authentication."""

    def test_settings_redirects_to_login(self, auth_client):
        response = auth_client.get("/settings")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_settings_accessible_after_login(self, auth_client):
        _login(auth_client)
        response = auth_client.get("/settings")
        assert response.status_code == 200

    def test_post_config_requires_auth(self, auth_client):
        response = auth_client.post(
            "/api/config",
            json={"theme": "team_colors"},
            content_type="application/json",
        )
        assert response.status_code == 401

    def test_post_config_works_after_login(self, auth_client):
        _login(auth_client)
        # Get CSRF token from session
        with auth_client.session_transaction() as sess:
            csrf = sess.get("csrf_token", "")
        response = auth_client.post(
            "/api/config",
            json={"theme": "team_colors"},
            content_type="application/json",
            headers={"X-CSRF-Token": csrf},
        )
        assert response.status_code == 200

    def test_get_config_is_public(self, auth_client):
        response = auth_client.get("/api/config")
        assert response.status_code == 200

    def test_get_status_is_public(self, auth_client):
        response = auth_client.get("/api/config/status")
        assert response.status_code == 200


@pytest.mark.integration
class TestNoAuthMode:
    """Tests for when authentication is disabled."""

    def test_settings_accessible_without_login(self, noauth_client):
        response = noauth_client.get("/settings")
        assert response.status_code == 200

    def test_post_config_works_without_login(self, noauth_client):
        response = noauth_client.post(
            "/api/config",
            json={"theme": "team_colors"},
            content_type="application/json",
        )
        assert response.status_code == 200


@pytest.mark.integration
class TestCSRFProtection:
    """Tests for CSRF token validation."""

    def test_post_rejected_without_csrf_token(self, auth_client):
        _login(auth_client)
        response = auth_client.post(
            "/api/config",
            json={"theme": "team_colors"},
            content_type="application/json",
        )
        assert response.status_code == 403
        data = response.get_json()
        assert "CSRF" in data["error"]

    def test_post_accepted_with_valid_csrf(self, auth_client):
        _login(auth_client)
        with auth_client.session_transaction() as sess:
            csrf = sess.get("csrf_token", "")
        response = auth_client.post(
            "/api/config",
            json={"theme": "team_colors"},
            content_type="application/json",
            headers={"X-CSRF-Token": csrf},
        )
        assert response.status_code == 200

    def test_post_rejected_with_wrong_csrf(self, auth_client):
        _login(auth_client)
        response = auth_client.post(
            "/api/config",
            json={"theme": "team_colors"},
            content_type="application/json",
            headers={"X-CSRF-Token": "wrong-token"},
        )
        assert response.status_code == 403
