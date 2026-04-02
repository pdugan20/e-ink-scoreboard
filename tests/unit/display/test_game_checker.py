"""
Unit tests for GameChecker class.

Tests game status checking, caching, circuit breaker, and screensaver logic.
"""

import time
from unittest.mock import Mock, mock_open, patch

import pytest
import requests
from freezegun import freeze_time

import src.config.game_status as game_status_module
from src.display.game_checker import GameChecker, load_game_status_config


@pytest.mark.unit
class TestLoadGameStatusConfig:
    """Tests for loading game status configuration"""

    def setup_method(self):
        """Clear the module-level cache before each test."""
        game_status_module._config_cache = None

    def test_load_game_status_config_success(self):
        """Test successful loading of game status config"""
        # Arrange
        mock_config = """
        {
            "activeGameStatuses": ["in progress", "top "],
            "scheduledGameStatuses": ["pm et", "scheduled"],
            "finalGameStatuses": ["final", "completed"]
        }
        """

        with patch("builtins.open", mock_open(read_data=mock_config)):
            # Act
            config = load_game_status_config()

        # Assert
        assert "activeGameStatuses" in config
        assert "in progress" in config["activeGameStatuses"]
        assert "scheduledGameStatuses" in config
        assert "finalGameStatuses" in config

    def test_load_game_status_config_file_not_found(self):
        """Test handling when config file doesn't exist"""
        # Arrange
        with patch("builtins.open", side_effect=FileNotFoundError()):
            # Act & Assert
            with pytest.raises(FileNotFoundError):
                load_game_status_config()


@pytest.mark.unit
class TestGameCheckerInit:
    """Tests for GameChecker initialization"""

    def test_init_sets_urls(self):
        """Test that initialization sets correct URLs"""
        # Act
        checker = GameChecker("http://localhost:5000/display")

        # Assert
        assert checker.web_server_url == "http://localhost:5000/display"
        assert checker.base_url == "http://localhost:5000"

    def test_init_creates_session(self):
        """Test that initialization creates a requests session"""
        # Act
        checker = GameChecker("http://localhost:5000/display")

        # Assert
        assert checker._session is not None
        assert isinstance(checker._session, requests.Session)

    def test_init_sets_circuit_breaker_defaults(self):
        """Test that circuit breaker values are initialized"""
        # Act
        checker = GameChecker("http://localhost:5000/display")

        # Assert
        assert checker._api_failure_count == 0
        assert checker._api_failure_threshold == 3
        assert checker._circuit_open_until == 0


@pytest.mark.unit
class TestGetGameState:
    """Tests for get_game_state method"""

    @freeze_time("2024-09-15 12:00:00")
    @patch("src.display.game_checker.load_game_status_config")
    def test_get_game_state_cache_hit(self, mock_load_config, requests_mock):
        """Test that game state is cached for 30 seconds"""
        # Arrange
        mock_load_config.return_value = {
            "activeGameStatuses": ["in progress"],
            "scheduledGameStatuses": ["pm et"],
            "finalGameStatuses": ["final"],
        }

        checker = GameChecker("http://localhost:5000/display")

        # First call - API returns data
        requests_mock.get(
            "http://localhost:5000/api/scores/MLB",
            json=[
                {
                    "status": "In Progress",
                    "away_team": "Yankees",
                    "home_team": "Red Sox",
                }
            ],
        )

        # Act - First call (cache miss)
        state1 = checker.get_game_state()

        # Change mock to return different data
        requests_mock.get(
            "http://localhost:5000/api/scores/MLB",
            json=[],
        )

        # Act - Second call within 30 seconds (cache hit)
        with freeze_time("2024-09-15 12:00:15"):  # 15 seconds later
            state2 = checker.get_game_state()

        # Assert - Should get cached state, not new data
        assert state1 == state2
        assert state2["has_active_games"] is True
        assert len(state2["active_games"]) == 1

    @freeze_time("2024-09-15 12:00:00")
    @patch("src.display.game_checker.load_game_status_config")
    def test_get_game_state_cache_miss(self, mock_load_config, requests_mock):
        """Test that game state cache expires after 30 seconds"""
        # Arrange
        mock_load_config.return_value = {
            "activeGameStatuses": ["in progress"],
            "scheduledGameStatuses": ["pm et"],
            "finalGameStatuses": ["final"],
        }

        checker = GameChecker("http://localhost:5000/display")

        requests_mock.get(
            "http://localhost:5000/api/scores/MLB",
            json=[{"status": "In Progress"}],
        )

        # First call
        state1 = checker.get_game_state()

        # Change response
        requests_mock.get(
            "http://localhost:5000/api/scores/MLB",
            json=[],
        )

        # Act - Second call after 30+ seconds (cache miss)
        with freeze_time("2024-09-15 12:00:31"):  # 31 seconds later
            state2 = checker.get_game_state()

        # Assert - Should get new data
        assert state1 != state2
        assert state1["has_active_games"] is True
        assert state2["has_active_games"] is False

    @freeze_time("2024-09-15 12:00:00")
    @patch("src.display.game_checker.load_game_status_config")
    def test_get_game_state_date_rollover_clears_cache(
        self, mock_load_config, requests_mock
    ):
        """Test that cache is cleared when date changes"""
        # Arrange
        mock_load_config.return_value = {
            "activeGameStatuses": ["in progress"],
            "scheduledGameStatuses": ["pm et"],
            "finalGameStatuses": ["final"],
        }

        checker = GameChecker("http://localhost:5000/display")

        requests_mock.get(
            "http://localhost:5000/api/scores/MLB",
            json=[{"status": "In Progress"}],
        )

        # First call on Sept 15
        state1 = checker.get_game_state()
        assert state1["has_active_games"] is True

        # Change to new day
        requests_mock.get(
            "http://localhost:5000/api/scores/MLB",
            json=[],
        )

        # Act - Call on Sept 16 (new date)
        with freeze_time("2024-09-16 00:00:01"):
            state2 = checker.get_game_state()

        # Assert - Cache should be cleared, new data fetched
        assert checker._last_cache_date == "2024-09-16"
        assert state2["has_active_games"] is False

    @freeze_time("2024-09-15 12:00:00")
    @patch("src.display.game_checker.load_game_status_config")
    def test_get_game_state_categorizes_games(self, mock_load_config, requests_mock):
        """Test that games are correctly categorized by status"""
        # Arrange
        mock_load_config.return_value = {
            "activeGameStatuses": ["in progress", "top ", "bottom "],
            "scheduledGameStatuses": ["pm et", "scheduled"],
            "finalGameStatuses": ["final"],
        }

        checker = GameChecker("http://localhost:5000/display")

        requests_mock.get(
            "http://localhost:5000/api/scores/MLB",
            json=[
                {"status": "In Progress", "game": 1},
                {"status": "Top 7th", "game": 2},
                {"status": "7:05 PM ET", "game": 3},
                {"status": "Final", "game": 4},
                {"status": "Bottom 3rd", "game": 5},
            ],
        )

        # Act
        state = checker.get_game_state()

        # Assert
        assert state["has_active_games"] is True
        assert state["has_any_games"] is True
        assert len(state["active_games"]) == 3  # In Progress, Top 7th, Bottom 3rd
        assert len(state["scheduled_games"]) == 1  # 7:05 PM ET
        assert len(state["final_games"]) == 1  # Final
        assert len(state["games"]) == 5

    @freeze_time("2024-09-15 12:00:00")
    @patch("src.display.game_checker.load_game_status_config")
    def test_get_game_state_unknown_status_treated_as_active(
        self, mock_load_config, requests_mock
    ):
        """Test that unknown game statuses are treated as active"""
        # Arrange
        mock_load_config.return_value = {
            "activeGameStatuses": ["in progress"],
            "scheduledGameStatuses": ["pm et"],
            "finalGameStatuses": ["final"],
        }

        checker = GameChecker("http://localhost:5000/display")

        requests_mock.get(
            "http://localhost:5000/api/scores/MLB",
            json=[
                {"status": "Unknown Status", "game": 1},
            ],
        )

        # Act
        state = checker.get_game_state()

        # Assert - Unknown status should be in active_games
        assert state["has_active_games"] is True
        assert len(state["active_games"]) == 1

    @freeze_time("2024-09-15 12:00:00")
    @patch("src.display.game_checker.load_game_status_config")
    def test_get_game_state_api_failure_returns_fallback(
        self, mock_load_config, requests_mock
    ):
        """Test that API failure returns fallback state"""
        # Arrange
        mock_load_config.return_value = {
            "activeGameStatuses": ["in progress"],
            "scheduledGameStatuses": ["pm et"],
            "finalGameStatuses": ["final"],
        }

        checker = GameChecker("http://localhost:5000/display")

        requests_mock.get(
            "http://localhost:5000/api/scores/MLB",
            status_code=500,
        )

        # Act
        state = checker.get_game_state()

        # Assert
        assert state["has_active_games"] is False
        assert state["has_any_games"] is False
        assert state["games"] == []

    @freeze_time("2024-09-15 12:00:00")
    @patch("src.display.game_checker.load_game_status_config")
    def test_get_game_state_timeout_returns_fallback(
        self, mock_load_config, requests_mock
    ):
        """Test that API timeout returns fallback state"""
        # Arrange
        mock_load_config.return_value = {
            "activeGameStatuses": ["in progress"],
            "scheduledGameStatuses": ["pm et"],
            "finalGameStatuses": ["final"],
        }

        checker = GameChecker("http://localhost:5000/display")

        requests_mock.get(
            "http://localhost:5000/api/scores/MLB",
            exc=requests.exceptions.Timeout,
        )

        # Act
        state = checker.get_game_state()

        # Assert
        assert state["has_active_games"] is False
        assert state["has_any_games"] is False

    @freeze_time("2024-09-15 12:00:00")
    @patch("src.display.game_checker.load_game_status_config")
    def test_get_game_state_circuit_breaker_opens_after_threshold(
        self, mock_load_config, requests_mock
    ):
        """Test that circuit breaker opens after failure threshold"""
        # Arrange
        mock_load_config.return_value = {
            "activeGameStatuses": ["in progress"],
            "scheduledGameStatuses": ["pm et"],
            "finalGameStatuses": ["final"],
        }

        checker = GameChecker("http://localhost:5000/display")

        requests_mock.get(
            "http://localhost:5000/api/scores/MLB",
            status_code=500,
        )

        # Act - Trigger 3 failures
        for i in range(3):
            checker.get_game_state()
            with freeze_time(f"2024-09-15 12:0{i}:35"):  # Move past cache time
                pass

        # Assert
        assert checker._api_failure_count == 3
        assert checker._circuit_open_until > time.time()

    @freeze_time("2024-09-15 12:00:00")
    @patch("src.display.game_checker.load_game_status_config")
    def test_get_game_state_circuit_breaker_prevents_api_calls(
        self, mock_load_config, requests_mock
    ):
        """Test that circuit breaker prevents API calls when open"""
        # Arrange
        mock_load_config.return_value = {
            "activeGameStatuses": ["in progress"],
            "scheduledGameStatuses": ["pm et"],
            "finalGameStatuses": ["final"],
        }

        checker = GameChecker("http://localhost:5000/display")

        # Manually open circuit
        checker._circuit_open_until = time.time() + 300

        # This should NOT be called because circuit is open
        mock_get = requests_mock.get(
            "http://localhost:5000/api/scores/MLB",
            json=[{"status": "In Progress"}],
        )

        # Act
        state = checker.get_game_state()

        # Assert
        assert mock_get.call_count == 0  # API should not be called
        assert state["has_active_games"] is False  # Fallback state

    @freeze_time("2024-09-15 12:00:00")
    @patch("src.display.game_checker.load_game_status_config")
    def test_get_game_state_resets_failure_count_on_success(
        self, mock_load_config, requests_mock
    ):
        """Test that failure count resets on successful API call"""
        # Arrange
        mock_load_config.return_value = {
            "activeGameStatuses": ["in progress"],
            "scheduledGameStatuses": ["pm et"],
            "finalGameStatuses": ["final"],
        }

        checker = GameChecker("http://localhost:5000/display")

        # Simulate 2 failures
        checker._api_failure_count = 2

        # Mock successful response
        requests_mock.get(
            "http://localhost:5000/api/scores/MLB",
            json=[{"status": "In Progress"}],
        )

        # Act
        checker.get_game_state()

        # Assert
        assert checker._api_failure_count == 0


@pytest.mark.unit
class TestGetFallbackGameState:
    """Tests for _get_fallback_game_state method"""

    @freeze_time("2024-09-15 12:00:00")
    def test_fallback_returns_cached_state_same_date(self):
        """Test that fallback returns cached state for same date"""
        # Arrange
        checker = GameChecker("http://localhost:5000/display")
        cached_state = {
            "has_active_games": True,
            "games": [{"status": "In Progress"}],
        }
        checker._last_game_state = cached_state
        checker._last_cache_date = "2024-09-15"

        # Act
        state = checker._get_fallback_game_state("2024-09-15")

        # Assert
        assert state == cached_state
        assert state["has_active_games"] is True

    @freeze_time("2024-09-16 12:00:00")
    def test_fallback_returns_empty_state_new_date(self):
        """Test that fallback returns empty state for new date"""
        # Arrange
        checker = GameChecker("http://localhost:5000/display")
        checker._last_game_state = {"has_active_games": True}
        checker._last_cache_date = "2024-09-15"  # Yesterday

        # Act
        state = checker._get_fallback_game_state("2024-09-16")  # Today

        # Assert
        assert state["has_active_games"] is False
        assert state["has_any_games"] is False
        assert state["games"] == []


@pytest.mark.unit
class TestCheckMethods:
    """Tests for check_* wrapper methods"""

    @patch.object(GameChecker, "get_game_state")
    def test_check_active_games_returns_true(self, mock_get_state):
        """Test check_active_games when active games exist"""
        # Arrange
        mock_get_state.return_value = {"has_active_games": True}
        checker = GameChecker("http://localhost:5000/display")

        # Act
        result = checker.check_active_games()

        # Assert
        assert result is True

    @patch.object(GameChecker, "get_game_state")
    def test_check_active_games_returns_false(self, mock_get_state):
        """Test check_active_games when no active games"""
        # Arrange
        mock_get_state.return_value = {"has_active_games": False}
        checker = GameChecker("http://localhost:5000/display")

        # Act
        result = checker.check_active_games()

        # Assert
        assert result is False

    @patch.object(GameChecker, "get_game_state")
    def test_check_any_games_today_returns_true(self, mock_get_state):
        """Test check_any_games_today when games exist"""
        # Arrange
        mock_get_state.return_value = {"has_any_games": True}
        checker = GameChecker("http://localhost:5000/display")

        # Act
        result = checker.check_any_games_today()

        # Assert
        assert result is True

    @patch.object(GameChecker, "get_game_state")
    def test_check_scheduled_games_returns_list(self, mock_get_state):
        """Test check_scheduled_games returns scheduled games list"""
        # Arrange
        scheduled = [{"status": "7:05 PM ET"}]
        mock_get_state.return_value = {"scheduled_games": scheduled}
        checker = GameChecker("http://localhost:5000/display")

        # Act
        result = checker.check_scheduled_games()

        # Assert
        assert result == scheduled


@pytest.mark.unit
class TestCheckScreensaverEligible:
    """Tests for check_screensaver_eligible method"""

    def test_screensaver_eligible_with_valid_article(self, requests_mock):
        """Test screensaver is eligible when article data is valid"""
        # Arrange
        checker = GameChecker("http://localhost:5000/display")

        requests_mock.get(
            "http://localhost:5000/api/screensaver/mlb",
            json={
                "title": "Mariners Win Big",
                "image_url": "https://example.com/image.jpg",
                "description": "Great game",
            },
        )

        # Act
        result = checker.check_screensaver_eligible()

        # Assert - Result is truthy (may be string or True)
        assert result

    def test_screensaver_not_eligible_missing_title(self, requests_mock):
        """Test screensaver is not eligible when title is missing"""
        # Arrange
        checker = GameChecker("http://localhost:5000/display")

        requests_mock.get(
            "http://localhost:5000/api/screensaver/mlb",
            json={
                "image_url": "https://example.com/image.jpg",
            },
        )

        # Act
        result = checker.check_screensaver_eligible()

        # Assert - Result is falsy
        assert not result

    def test_screensaver_not_eligible_missing_image(self, requests_mock):
        """Test screensaver is not eligible when image_url is missing"""
        # Arrange
        checker = GameChecker("http://localhost:5000/display")

        requests_mock.get(
            "http://localhost:5000/api/screensaver/mlb",
            json={
                "title": "Mariners Win Big",
            },
        )

        # Act
        result = checker.check_screensaver_eligible()

        # Assert - Result is falsy
        assert not result

    def test_screensaver_not_eligible_empty_response(self, requests_mock):
        """Test screensaver is not eligible when response is empty"""
        # Arrange
        checker = GameChecker("http://localhost:5000/display")

        requests_mock.get(
            "http://localhost:5000/api/screensaver/mlb",
            json={},
        )

        # Act
        result = checker.check_screensaver_eligible()

        # Assert - Result is falsy
        assert not result

    def test_screensaver_not_eligible_api_failure(self, requests_mock):
        """Test screensaver is not eligible when API fails"""
        # Arrange
        checker = GameChecker("http://localhost:5000/display")

        requests_mock.get(
            "http://localhost:5000/api/screensaver/mlb",
            status_code=404,
        )

        # Act
        result = checker.check_screensaver_eligible()

        # Assert
        assert result is False

    def test_screensaver_not_eligible_timeout(self, requests_mock):
        """Test screensaver is not eligible when API times out"""
        # Arrange
        checker = GameChecker("http://localhost:5000/display")

        requests_mock.get(
            "http://localhost:5000/api/screensaver/mlb",
            exc=requests.exceptions.Timeout,
        )

        # Act
        result = checker.check_screensaver_eligible()

        # Assert
        assert result is False


@pytest.mark.unit
class TestCleanup:
    """Tests for cleanup and resource management"""

    def test_cleanup_closes_session(self):
        """Test that cleanup closes the requests session"""
        # Arrange
        checker = GameChecker("http://localhost:5000/display")
        mock_session = Mock()
        checker._session = mock_session

        # Act
        checker.cleanup()

        # Assert
        mock_session.close.assert_called_once()

    def test_cleanup_handles_errors(self):
        """Test that cleanup handles errors gracefully"""
        # Arrange
        checker = GameChecker("http://localhost:5000/display")
        mock_session = Mock()
        mock_session.close.side_effect = Exception("Close failed")
        checker._session = mock_session

        # Act - Should not raise exception
        checker.cleanup()

        # Assert
        mock_session.close.assert_called_once()


@pytest.mark.unit
class TestWrappedApiResponse:
    """Tests for handling the wrapped scores API response format."""

    @freeze_time("2024-09-15 12:00:00")
    @patch("src.display.game_checker.load_game_status_config")
    def test_unwraps_dict_response(self, mock_load_config, requests_mock):
        """Test that wrapped response { games: [...] } is unwrapped correctly."""
        mock_load_config.return_value = {
            "activeGameStatuses": ["in progress"],
            "scheduledGameStatuses": ["pm et"],
            "finalGameStatuses": ["final"],
        }

        checker = GameChecker("http://localhost:5000/display")

        requests_mock.get(
            "http://localhost:5000/api/scores/MLB",
            json={
                "games": [
                    {"status": "Final", "away_team": "Yankees", "home_team": "Red Sox"}
                ],
                "all_games_final": True,
            },
        )

        state = checker.get_game_state()
        assert state["has_any_games"] is True
        assert len(state["final_games"]) == 1

    @freeze_time("2024-09-15 12:00:00")
    @patch("src.display.game_checker.load_game_status_config")
    def test_handles_raw_list_response(self, mock_load_config, requests_mock):
        """Test backward compatibility with raw list response."""
        mock_load_config.return_value = {
            "activeGameStatuses": ["in progress"],
            "scheduledGameStatuses": ["pm et"],
            "finalGameStatuses": ["final"],
        }

        checker = GameChecker("http://localhost:5000/display")

        requests_mock.get(
            "http://localhost:5000/api/scores/MLB",
            json=[{"status": "In Progress", "away_team": "Cubs", "home_team": "Mets"}],
        )

        state = checker.get_game_state()
        assert state["has_any_games"] is True
        assert len(state["active_games"]) == 1
