"""
Unit tests for the configuration API.

Tests config file parsing, validation, and read/write round-trips.
"""

import json

import pytest

from src.api import config_api
from src.api.config_api import (
    read_eink_config,
    read_js_config,
    validate_config,
    write_eink_config,
    write_js_config,
)

# Sample config.js content for testing
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

// Screensaver mode constants
export const SCREENSAVER_MODES = {
  OFF: 'off',
  NO_GAMES: 'no_games',
  AFTER_LAST_GAME: 'after_last_game',
};

// Screensaver mode configuration
export const screensaverMode = SCREENSAVER_MODES.NO_GAMES;
"""

SAMPLE_EINK_CONFIG = {
    "web_server_url": "http://localhost:5001/display",
    "screenshot_path": "/tmp/sports_display.png",
    "display_width": 800,
    "display_height": 480,
    "screenshot_scale": 1,
    "refresh_interval": 360,
    "apply_dithering": False,
    "logging": {
        "level": "INFO",
        "log_file": "~/logs/eink_display.log",
    },
}


@pytest.fixture
def config_dir(tmp_path):
    """Create temporary config files and point the module at them."""
    # Write sample config.js
    js_path = tmp_path / "config.js"
    js_path.write_text(SAMPLE_JS_CONFIG)

    # Write sample eink_config.json
    eink_path = tmp_path / "eink_config.json"
    eink_path.write_text(json.dumps(SAMPLE_EINK_CONFIG, indent=2))

    # Monkey-patch the module paths
    original_js = config_api.JS_CONFIG_PATH
    original_eink = config_api.EINK_CONFIG_PATH
    config_api.JS_CONFIG_PATH = str(js_path)
    config_api.EINK_CONFIG_PATH = str(eink_path)

    yield tmp_path

    # Restore original paths
    config_api.JS_CONFIG_PATH = original_js
    config_api.EINK_CONFIG_PATH = original_eink


@pytest.mark.unit
class TestReadJsConfig:
    """Tests for parsing config.js"""

    def test_reads_feature_flags(self, config_dir):
        config = read_js_config()
        assert config["show_standings"] is False
        assert config["eink_optimized_contrast"] is True
        assert config["show_screensaver"] is True

    def test_reads_favorite_teams(self, config_dir):
        config = read_js_config()
        assert config["favorite_teams"] == ["Seattle Mariners"]

    def test_reads_timezone(self, config_dir):
        config = read_js_config()
        assert config["timezone"] == "America/Los_Angeles"

    def test_reads_theme(self, config_dir):
        config = read_js_config()
        assert config["theme"] == "default"

    def test_reads_null_teams_as_empty_list(self, config_dir):
        js_path = config_dir / "config.js"
        content = js_path.read_text()
        content = content.replace("mlb: ['Seattle Mariners']", "mlb: null")
        js_path.write_text(content)

        config = read_js_config()
        assert config["favorite_teams"] == []

    def test_reads_multiple_teams(self, config_dir):
        js_path = config_dir / "config.js"
        content = js_path.read_text()
        content = content.replace(
            "mlb: ['Seattle Mariners']",
            "mlb: ['Seattle Mariners', 'New York Yankees']",
        )
        js_path.write_text(content)

        config = read_js_config()
        assert config["favorite_teams"] == [
            "Seattle Mariners",
            "New York Yankees",
        ]

    def test_reads_custom_timezone(self, config_dir):
        js_path = config_dir / "config.js"
        content = js_path.read_text()
        content = content.replace(
            "export const displayTimezone = TIMEZONES.PACIFIC;",
            "export const displayTimezone = 'Europe/London';",
        )
        js_path.write_text(content)

        config = read_js_config()
        assert config["timezone"] == "Europe/London"


@pytest.mark.unit
class TestWriteJsConfig:
    """Tests for writing config.js"""

    def test_updates_timezone(self, config_dir):
        write_js_config({"timezone": "America/New_York"})
        config = read_js_config()
        assert config["timezone"] == "America/New_York"

    def test_updates_theme(self, config_dir):
        write_js_config({"theme": "team_colors"})
        config = read_js_config()
        assert config["theme"] == "team_colors"

    def test_updates_favorite_teams(self, config_dir):
        write_js_config({"favorite_teams": ["New York Yankees", "Boston Red Sox"]})
        config = read_js_config()
        assert config["favorite_teams"] == [
            "New York Yankees",
            "Boston Red Sox",
        ]

    def test_clears_favorite_teams(self, config_dir):
        write_js_config({"favorite_teams": []})
        config = read_js_config()
        assert config["favorite_teams"] == []

    def test_updates_feature_flags(self, config_dir):
        write_js_config({"show_screensaver": False})
        config = read_js_config()
        assert config["show_screensaver"] is False
        # Other flags should be preserved
        assert config["eink_optimized_contrast"] is True

    def test_preserves_unmodified_values(self, config_dir):
        write_js_config({"theme": "mlb_scoreboard"})
        config = read_js_config()
        # Theme changed
        assert config["theme"] == "mlb_scoreboard"
        # Others preserved
        assert config["timezone"] == "America/Los_Angeles"
        assert config["favorite_teams"] == ["Seattle Mariners"]

    def test_writes_custom_timezone(self, config_dir):
        write_js_config({"timezone": "Europe/London"})
        # Verify it's written as a quoted string (not a TIMEZONES constant)
        js_path = config_dir / "config.js"
        content = js_path.read_text()
        assert "'Europe/London'" in content

    def test_writes_known_timezone_as_constant(self, config_dir):
        write_js_config({"timezone": "America/Chicago"})
        js_path = config_dir / "config.js"
        content = js_path.read_text()
        assert "TIMEZONES.CENTRAL" in content


@pytest.mark.unit
class TestReadEinkConfig:
    """Tests for reading eink_config.json"""

    def test_reads_refresh_interval(self, config_dir):
        config = read_eink_config()
        assert config["refresh_interval"] == 360

    def test_reads_all_fields(self, config_dir):
        config = read_eink_config()
        assert config["display_width"] == 800
        assert config["display_height"] == 480


@pytest.mark.unit
class TestWriteEinkConfig:
    """Tests for writing eink_config.json"""

    def test_updates_refresh_interval(self, config_dir):
        config = read_eink_config()
        config["refresh_interval"] = 900
        write_eink_config(config)

        updated = read_eink_config()
        assert updated["refresh_interval"] == 900

    def test_preserves_other_fields(self, config_dir):
        config = read_eink_config()
        config["refresh_interval"] = 1800
        write_eink_config(config)

        updated = read_eink_config()
        assert updated["display_width"] == 800
        assert updated["web_server_url"] == "http://localhost:5001/display"


@pytest.mark.unit
class TestValidateConfig:
    """Tests for input validation"""

    def test_valid_config(self):
        errors = validate_config(
            {
                "refresh_interval": 360,
                "favorite_teams": ["Seattle Mariners"],
                "timezone": "America/Los_Angeles",
                "theme": "default",
                "show_screensaver": True,
            }
        )
        assert errors == []

    def test_invalid_refresh_interval_too_low(self):
        errors = validate_config({"refresh_interval": 10})
        assert len(errors) == 1
        assert "between 60 and 3600" in errors[0]

    def test_invalid_refresh_interval_too_high(self):
        errors = validate_config({"refresh_interval": 9999})
        assert len(errors) == 1

    def test_invalid_refresh_interval_not_number(self):
        errors = validate_config({"refresh_interval": "fast"})
        assert len(errors) == 1
        assert "must be a number" in errors[0]

    def test_invalid_team_name(self):
        errors = validate_config({"favorite_teams": ["Fake Team"]})
        assert len(errors) == 1
        assert "Invalid team names" in errors[0]

    def test_invalid_theme(self):
        errors = validate_config({"theme": "neon"})
        assert len(errors) == 1
        assert "Invalid theme" in errors[0]

    def test_invalid_boolean_field(self):
        errors = validate_config({"show_screensaver": "yes"})
        assert len(errors) == 1
        assert "must be a boolean" in errors[0]

    def test_empty_teams_list_valid(self):
        errors = validate_config({"favorite_teams": []})
        assert errors == []

    def test_custom_timezone_valid(self):
        errors = validate_config({"timezone": "Europe/London"})
        assert errors == []


@pytest.mark.unit
class TestRoundTrip:
    """Tests for reading, modifying, and re-reading config."""

    def test_full_config_round_trip(self, config_dir):
        # Read original
        original_eink = read_eink_config()

        # Modify everything
        write_js_config(
            {
                "favorite_teams": ["Chicago Cubs", "New York Mets"],
                "timezone": "America/New_York",
                "theme": "mlb_scoreboard",
                "show_screensaver": False,
                "eink_optimized_contrast": False,
            }
        )
        original_eink["refresh_interval"] = 1800
        write_eink_config(original_eink)

        # Re-read and verify
        updated_js = read_js_config()
        updated_eink = read_eink_config()

        assert updated_js["favorite_teams"] == ["Chicago Cubs", "New York Mets"]
        assert updated_js["timezone"] == "America/New_York"
        assert updated_js["theme"] == "mlb_scoreboard"
        assert updated_js["show_screensaver"] is False
        assert updated_js["eink_optimized_contrast"] is False
        assert updated_eink["refresh_interval"] == 1800


@pytest.mark.unit
class TestScreensaverConfig:
    """Tests for screensaver mode config reading, writing, and validation."""

    def test_reads_screensaver_mode(self, config_dir):
        config = read_js_config()
        assert config["screensaver_mode"] == "no_games"

    def test_writes_screensaver_mode(self, config_dir):
        write_js_config({"screensaver_mode": "after_last_game"})
        config = read_js_config()
        assert config["screensaver_mode"] == "after_last_game"

    def test_writes_screensaver_mode_off(self, config_dir):
        write_js_config({"screensaver_mode": "off"})
        config = read_js_config()
        assert config["screensaver_mode"] == "off"

    def test_screensaver_mode_off_disables_show_screensaver(self, config_dir):
        """Setting screensaver_mode to 'off' should set SHOW_SCREENSAVER to false."""
        write_js_config({"screensaver_mode": "off"})
        config = read_js_config()
        assert config["show_screensaver"] is False

    def test_screensaver_mode_no_games_enables_show_screensaver(self, config_dir):
        """Setting screensaver_mode to 'no_games' should set SHOW_SCREENSAVER to true."""
        # First set to off
        write_js_config({"screensaver_mode": "off"})
        # Then back to no_games
        write_js_config({"screensaver_mode": "no_games"})
        config = read_js_config()
        assert config["show_screensaver"] is True

    def test_writes_screensaver_mode_as_constant(self, config_dir):
        write_js_config({"screensaver_mode": "after_last_game"})
        js_path = config_dir / "config.js"
        content = js_path.read_text()
        assert "SCREENSAVER_MODES.AFTER_LAST_GAME" in content

    def test_validate_invalid_screensaver_mode(self):
        errors = validate_config({"screensaver_mode": "always"})
        assert len(errors) == 1
        assert "screensaver_mode" in errors[0]

    def test_validate_valid_screensaver_mode(self):
        errors = validate_config({"screensaver_mode": "after_last_game"})
        assert errors == []

    def test_validate_invalid_screensaver_feed_type(self):
        errors = validate_config({"screensaver_feed_type": "video"})
        assert len(errors) == 1
        assert "screensaver_feed_type" in errors[0]

    def test_validate_valid_screensaver_feed_type(self):
        errors = validate_config({"screensaver_feed_type": "both"})
        assert errors == []

    def test_screensaver_mode_round_trip(self, config_dir):
        """Write screensaver_mode, read it back, verify all values."""
        write_js_config({"screensaver_mode": "after_last_game"})
        config = read_js_config()
        assert config["screensaver_mode"] == "after_last_game"
        # Other values preserved
        assert config["timezone"] == "America/Los_Angeles"
        assert config["theme"] == "default"
