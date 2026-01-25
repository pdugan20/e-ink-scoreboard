"""
Unit tests for screensaver API functions.

Tests the screensaver API config parsing logic.
"""

from unittest.mock import mock_open, patch

import pytest

from src.api.screensaver_api import (
    get_favorite_teams_from_config,
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


# Note: ScreensaverService integration tests have been moved to
# tests/integration/test_screensaver_integration.py
# Only config parsing is tested here in unit tests
