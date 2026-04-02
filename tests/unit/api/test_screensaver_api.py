"""
Unit tests for screensaver API functions.

Tests the screensaver API config parsing logic and fallback behavior.
"""

from unittest.mock import mock_open, patch

import pytest

from src.api.screensaver_api import (
    get_favorite_teams_from_config,
    get_screensaver_data_with_fallback,
)


@pytest.mark.unit
class TestFavoriteTeamsConfig:
    """Tests for favorite teams config parsing"""

    def test_parse_favorite_teams_single_team(self):
        """Test parsing config with single favorite team"""
        # Arrange
        mock_config = """
        const favoriteTeams = {
            mlb: ['Seattle Mariners'],
            nfl: null,
        };
        """

        with patch("builtins.open", mock_open(read_data=mock_config)):
            # Act
            teams = get_favorite_teams_from_config()

        # Assert
        assert teams == {
            "mlb": ["Seattle Mariners"],
            "nfl": [],
        }

    def test_parse_favorite_teams_multiple_teams(self):
        """Test parsing config with multiple favorite teams"""
        # Arrange
        mock_config = """
        const favoriteTeams = {
            mlb: ['Seattle Mariners', 'New York Yankees'],
            nfl: ['Buffalo Bills', 'Kansas City Chiefs'],
        };
        """

        with patch("builtins.open", mock_open(read_data=mock_config)):
            # Act
            teams = get_favorite_teams_from_config()

        # Assert
        assert teams == {
            "mlb": ["Seattle Mariners", "New York Yankees"],
            "nfl": ["Buffalo Bills", "Kansas City Chiefs"],
        }

    def test_parse_favorite_teams_null_values(self):
        """Test parsing config with null values"""
        # Arrange
        mock_config = """
        const favoriteTeams = {
            mlb: null,
            nfl: null,
            nba: null,
        };
        """

        with patch("builtins.open", mock_open(read_data=mock_config)):
            # Act
            teams = get_favorite_teams_from_config()

        # Assert
        assert teams == {
            "mlb": [],
            "nfl": [],
            "nba": [],
        }

    def test_parse_favorite_teams_mixed_spacing(self):
        """Test parsing config with various spacing formats"""
        # Arrange
        mock_config = """
        const favoriteTeams={
            mlb:['Seattle Mariners'],
            nfl:   [  'Buffalo Bills'  ],
        };
        """

        with patch("builtins.open", mock_open(read_data=mock_config)):
            # Act
            teams = get_favorite_teams_from_config()

        # Assert
        assert teams["mlb"] == ["Seattle Mariners"]
        assert teams["nfl"] == ["Buffalo Bills"]

    def test_parse_favorite_teams_file_not_found(self):
        """Test handling when config file doesn't exist"""
        # Arrange
        with patch("builtins.open", side_effect=FileNotFoundError()):
            # Act
            teams = get_favorite_teams_from_config()

        # Assert
        assert teams == {}

    def test_parse_favorite_teams_invalid_format(self):
        """Test handling invalid config format"""
        # Arrange
        mock_config = """
        const something_else = {
            data: 'value'
        };
        """

        with patch("builtins.open", mock_open(read_data=mock_config)):
            # Act
            teams = get_favorite_teams_from_config()

        # Assert
        assert teams == {}

    def test_parse_favorite_teams_empty_arrays(self):
        """Test parsing config with empty arrays"""
        # Arrange
        mock_config = """
        const favoriteTeams = {
            mlb: [],
            nfl: [],
        };
        """

        with patch("builtins.open", mock_open(read_data=mock_config)):
            # Act
            teams = get_favorite_teams_from_config()

        # Assert
        assert teams == {
            "mlb": [],
            "nfl": [],
        }


@pytest.mark.unit
class TestScreensaverFallback:
    """Tests for feed type fallback logic."""

    @patch("src.api.screensaver_api.get_screensaver_data")
    def test_both_tries_photos_first(self, mock_get):
        """When feed_type is 'both', photos is tried first."""
        mock_get.side_effect = [
            {"title": "Photo", "image_url": "http://img.jpg", "feed_source": "photos"},
        ]
        result = get_screensaver_data_with_fallback("mlb", "both")
        assert result["feed_source"] == "photos"
        mock_get.assert_called_once_with("mlb", "photos")

    @patch("src.api.screensaver_api.get_screensaver_data")
    def test_both_falls_back_to_news(self, mock_get):
        """When photos fails in 'both' mode, falls back to news."""
        mock_get.side_effect = [
            {"error": "No photos", "title": None, "image_url": None},
            {"title": "Article", "image_url": "http://img.jpg", "feed_source": "news"},
        ]
        result = get_screensaver_data_with_fallback("mlb", "both")
        assert result["feed_source"] == "news"
        assert mock_get.call_count == 2

    @patch("src.api.screensaver_api.get_screensaver_data")
    def test_news_falls_back_to_photos(self, mock_get):
        """When news fails, falls back to photos."""
        mock_get.side_effect = [
            {"error": "No news", "title": None, "image_url": None},
            {"title": "Photo", "image_url": "http://img.jpg", "feed_source": "photos"},
        ]
        result = get_screensaver_data_with_fallback("mlb", "news")
        assert result["feed_source"] == "photos"

    @patch("src.api.screensaver_api.get_screensaver_data")
    def test_photos_falls_back_to_news(self, mock_get):
        """When photos fails, falls back to news."""
        mock_get.side_effect = [
            {"error": "No photos", "title": None, "image_url": None},
            {"title": "Article", "image_url": "http://img.jpg", "feed_source": "news"},
        ]
        result = get_screensaver_data_with_fallback("mlb", "photos")
        assert result["feed_source"] == "news"

    @patch("src.api.screensaver_api.get_screensaver_data")
    def test_both_fail_returns_last_error(self, mock_get):
        """When both sources fail, returns the last attempt's result."""
        mock_get.side_effect = [
            {"error": "No photos", "title": None, "image_url": None},
            {"error": "No news", "title": None, "image_url": None},
        ]
        result = get_screensaver_data_with_fallback("mlb", "both")
        assert "error" in result
