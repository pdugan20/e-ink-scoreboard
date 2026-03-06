"""
Integration tests for WiFi management API endpoints.
"""

import json
import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))

from api import auth, config_api  # noqa: E402
from dev_server import app  # noqa: E402

SAMPLE_JS_CONFIG = """\
export const FEATURE_FLAGS = { SHOW_STANDINGS: false, EINK_OPTIMIZED_CONTRAST: true, SHOW_SCREENSAVER: true };
export const favoriteTeams = { mlb: null, nfl: null, cfb: null };
export const TIMEZONES = { EASTERN: 'America/New_York', PACIFIC: 'America/Los_Angeles' };
export const displayTimezone = TIMEZONES.PACIFIC;
export const THEMES = { DEFAULT: 'default' };
export const currentTheme = THEMES.DEFAULT;
"""


@pytest.fixture
def client(tmp_path):
    """Create a test client with no auth (open access)."""
    js_path = tmp_path / "config.js"
    js_path.write_text(SAMPLE_JS_CONFIG)
    eink_path = tmp_path / "eink_config.json"
    eink_path.write_text(json.dumps({"refresh_interval": 360}))

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


@pytest.mark.integration
class TestWifiStatus:
    """Tests for GET /api/wifi/status."""

    def test_returns_connected_status(self, client):
        nmcli_output = "MyNetwork:wlan0:802-11-wireless\n"
        hostname_output = "192.168.1.100 \n"

        def fake_run(cmd, **kwargs):
            if cmd[0] == "nmcli" and cmd[1] == "--version":
                return type("R", (), {"returncode": 0})()
            if "con" in cmd:
                return type("R", (), {"stdout": nmcli_output, "returncode": 0})()
            if cmd[0] == "hostname":
                return type("R", (), {"stdout": hostname_output, "returncode": 0})()
            return type("R", (), {"stdout": "", "returncode": 0})()

        with patch("api.wifi_api.subprocess.run", side_effect=fake_run):
            response = client.get("/api/wifi/status")

        assert response.status_code == 200
        data = response.get_json()
        assert data["connected"] is True
        assert data["network"] == "MyNetwork"
        assert data["ip_address"] == "192.168.1.100"

    def test_returns_disconnected_status(self, client):
        def fake_run(cmd, **kwargs):
            if cmd[0] == "nmcli" and cmd[1] == "--version":
                return type("R", (), {"returncode": 0})()
            if cmd[0] == "hostname":
                return type("R", (), {"stdout": "", "returncode": 0})()
            return type("R", (), {"stdout": "", "returncode": 0})()

        with patch("api.wifi_api.subprocess.run", side_effect=fake_run):
            response = client.get("/api/wifi/status")

        assert response.status_code == 200
        data = response.get_json()
        assert data["connected"] is False
        assert data["network"] is None

    def test_returns_503_when_nmcli_missing(self, client):
        with patch("api.wifi_api.subprocess.run", side_effect=FileNotFoundError):
            response = client.get("/api/wifi/status")
        assert response.status_code == 503


@pytest.mark.integration
class TestWifiNetworks:
    """Tests for GET /api/wifi/networks."""

    def test_returns_network_list(self, client):
        scan_output = "HomeWifi:85:WPA2:*\nNeighborNet:42:WPA2:\nOpenCafe:30::\n"

        def fake_run(cmd, **kwargs):
            if cmd[0] == "nmcli" and cmd[1] == "--version":
                return type("R", (), {"returncode": 0})()
            if "rescan" in cmd:
                return type("R", (), {"returncode": 0})()
            if "list" in cmd:
                return type("R", (), {"stdout": scan_output, "returncode": 0})()
            return type("R", (), {"stdout": "", "returncode": 0})()

        with patch("api.wifi_api.subprocess.run", side_effect=fake_run):
            response = client.get("/api/wifi/networks")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["networks"]) == 3
        assert data["networks"][0]["ssid"] == "HomeWifi"
        assert data["networks"][0]["signal"] == 85
        assert data["networks"][0]["active"] is True
        assert data["networks"][1]["ssid"] == "NeighborNet"
        assert data["networks"][2]["security"] == "Open"

    def test_deduplicates_ssids(self, client):
        scan_output = "MyNet:80:WPA2:*\nMyNet:60:WPA2:\n"

        def fake_run(cmd, **kwargs):
            if cmd[0] == "nmcli" and cmd[1] == "--version":
                return type("R", (), {"returncode": 0})()
            if "list" in cmd:
                return type("R", (), {"stdout": scan_output, "returncode": 0})()
            return type("R", (), {"stdout": "", "returncode": 0})()

        with patch("api.wifi_api.subprocess.run", side_effect=fake_run):
            response = client.get("/api/wifi/networks")

        data = response.get_json()
        assert len(data["networks"]) == 1

    def test_returns_503_when_nmcli_missing(self, client):
        with patch("api.wifi_api.subprocess.run", side_effect=FileNotFoundError):
            response = client.get("/api/wifi/networks")
        assert response.status_code == 503


@pytest.mark.integration
class TestWifiConnect:
    """Tests for POST /api/wifi/connect."""

    def test_connect_success(self, client):
        mock_result = type(
            "R", (), {"stdout": "connected", "stderr": "", "returncode": 0}
        )()

        def fake_run(cmd, **kwargs):
            if cmd[0] == "nmcli" and cmd[1] == "--version":
                return type("R", (), {"returncode": 0})()
            return mock_result

        with patch("api.wifi_api.subprocess.run", side_effect=fake_run):
            response = client.post(
                "/api/wifi/connect",
                json={"ssid": "TestNetwork", "password": "secret123"},
                content_type="application/json",
            )

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
        assert data["ssid"] == "TestNetwork"

    def test_connect_failure(self, client):
        mock_result = type(
            "R", (), {"stdout": "", "stderr": "No network found", "returncode": 1}
        )()

        def fake_run(cmd, **kwargs):
            if cmd[0] == "nmcli" and cmd[1] == "--version":
                return type("R", (), {"returncode": 0})()
            return mock_result

        with patch("api.wifi_api.subprocess.run", side_effect=fake_run):
            response = client.post(
                "/api/wifi/connect",
                json={"ssid": "BadNetwork", "password": "wrong"},
                content_type="application/json",
            )

        assert response.status_code == 500
        assert "No network found" in response.get_json()["error"]

    def test_rejects_missing_ssid(self, client):
        response = client.post(
            "/api/wifi/connect",
            json={"password": "test"},
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_rejects_empty_ssid(self, client):
        response = client.post(
            "/api/wifi/connect",
            json={"ssid": "", "password": "test"},
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_rejects_invalid_ssid(self, client):
        response = client.post(
            "/api/wifi/connect",
            json={"ssid": "bad\x00ssid", "password": "test"},
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_returns_503_when_nmcli_missing(self, client):
        with patch("api.wifi_api.subprocess.run", side_effect=FileNotFoundError):
            response = client.post(
                "/api/wifi/connect",
                json={"ssid": "Test", "password": "pass"},
                content_type="application/json",
            )
        assert response.status_code == 503

    def test_handles_timeout(self, client):
        import subprocess

        def fake_run(cmd, **kwargs):
            if cmd[0] == "nmcli" and cmd[1] == "--version":
                return type("R", (), {"returncode": 0})()
            raise subprocess.TimeoutExpired("cmd", 30)

        with patch("api.wifi_api.subprocess.run", side_effect=fake_run):
            response = client.post(
                "/api/wifi/connect",
                json={"ssid": "SlowNet", "password": "pass"},
                content_type="application/json",
            )
        assert response.status_code == 504
