"""
Unit tests for RefreshController class.

Tests refresh timing, memory management, and display update logic.
"""

import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

# Mock the config module before importing RefreshController
sys.modules["config"] = MagicMock()
sys.modules["config.memory_config"] = MagicMock(MEMORY_STARTUP_WAIT_MB=100)
sys.modules["utils"] = MagicMock()
sys.modules["utils.logging_config"] = MagicMock()

from src.display.refresh_controller import RefreshController  # noqa: E402


@pytest.mark.unit
class TestRefreshControllerInit:
    """Tests for RefreshController initialization"""

    def test_init_sets_dependencies(self):
        """Test that initialization sets all dependencies"""
        # Arrange
        config = {"refresh_interval": 60}
        game_checker = Mock()
        screenshot_controller = Mock()

        # Act
        controller = RefreshController(config, game_checker, screenshot_controller)

        # Assert
        assert controller.config == config
        assert controller.game_checker == game_checker
        assert controller.screenshot_controller == screenshot_controller


@pytest.mark.unit
class TestWaitForMemoryOnStartup:
    """Tests for _wait_for_memory_on_startup method"""

    @patch("src.display.refresh_controller.psutil.virtual_memory")
    @patch("src.display.refresh_controller.MEMORY_STARTUP_WAIT_MB", 100)
    def test_sufficient_memory_immediately(self, mock_virtual_memory):
        """Test when sufficient memory is available immediately"""
        # Arrange
        mock_mem = Mock()
        mock_mem.available = 150 * 1024 * 1024  # 150 MB
        mock_virtual_memory.return_value = mock_mem

        controller = RefreshController({}, Mock(), Mock())

        # Act
        controller._wait_for_memory_on_startup()

        # Assert
        mock_virtual_memory.assert_called_once()

    @patch("src.display.refresh_controller.psutil.virtual_memory")
    @patch("src.display.refresh_controller.time.sleep")
    @patch("src.display.refresh_controller.MEMORY_STARTUP_WAIT_MB", 100)
    def test_wait_for_memory_then_succeed(self, mock_sleep, mock_virtual_memory):
        """Test waiting for memory to become available"""
        # Arrange
        # First two checks: insufficient memory, third check: sufficient
        mem_values = [
            Mock(available=50 * 1024 * 1024),  # 50 MB
            Mock(available=75 * 1024 * 1024),  # 75 MB
            Mock(available=150 * 1024 * 1024),  # 150 MB (sufficient)
        ]
        mock_virtual_memory.side_effect = mem_values

        controller = RefreshController({}, Mock(), Mock())

        # Act
        controller._wait_for_memory_on_startup()

        # Assert
        assert mock_virtual_memory.call_count == 3
        assert mock_sleep.call_count == 2  # Slept twice before success

    @patch("src.display.refresh_controller.psutil.virtual_memory")
    @patch("src.display.refresh_controller.time.sleep")
    @patch("src.display.refresh_controller.time.time")
    @patch("src.display.refresh_controller.MEMORY_STARTUP_WAIT_MB", 100)
    def test_timeout_after_max_wait(self, mock_time, mock_sleep, mock_virtual_memory):
        """Test that method times out after max wait time"""
        # Arrange
        # Simulate time passing (5 minutes = 300 seconds)
        # First call: start_time = 0
        # Second call: check in while loop = 301 (past timeout)
        # Additional calls from logger.warning() timestamp creation
        mock_time.side_effect = [0, 301, 301, 301, 301]

        controller = RefreshController({}, Mock(), Mock())

        # Act
        controller._wait_for_memory_on_startup()

        # Assert - Should exit due to timeout without checking memory
        # The while condition fails immediately, so virtual_memory is never called
        assert mock_time.call_count >= 2  # At least 2 calls for the timing logic

    @patch("src.display.refresh_controller.psutil.virtual_memory")
    def test_memory_check_error_proceeds_anyway(self, mock_virtual_memory):
        """Test that memory check errors allow the process to continue"""
        # Arrange
        mock_virtual_memory.side_effect = Exception("Memory check failed")

        controller = RefreshController({}, Mock(), Mock())

        # Act - Should not raise exception
        controller._wait_for_memory_on_startup()

        # Assert
        mock_virtual_memory.assert_called_once()


@pytest.mark.unit
class TestRefreshDisplay:
    """Tests for refresh_display method"""

    def test_refresh_display_force_update_true(self):
        """Test that force_update=True always updates display"""
        # Arrange
        config = {"max_retries": 3, "retry_delay": 1}
        game_checker = Mock()
        screenshot_controller = Mock()
        screenshot_controller.take_screenshot.return_value = True
        screenshot_controller.process_image.return_value = Mock()  # Fake image
        screenshot_controller.update_display.return_value = True

        controller = RefreshController(config, game_checker, screenshot_controller)

        # Act
        result = controller.refresh_display(force_update=True)

        # Assert
        assert result is True
        screenshot_controller.take_screenshot.assert_called_once()
        screenshot_controller.process_image.assert_called_once()
        screenshot_controller.update_display.assert_called_once()
        # Should NOT check for active games when force_update=True
        game_checker.check_active_games.assert_not_called()

    def test_refresh_display_with_active_games(self):
        """Test that display updates when there are active games"""
        # Arrange
        config = {"max_retries": 3, "retry_delay": 1}
        game_checker = Mock()
        game_checker.check_active_games.return_value = True  # Active games exist
        screenshot_controller = Mock()
        screenshot_controller.take_screenshot.return_value = True
        screenshot_controller.process_image.return_value = Mock()
        screenshot_controller.update_display.return_value = True

        controller = RefreshController(config, game_checker, screenshot_controller)

        # Act
        result = controller.refresh_display(force_update=False)

        # Assert
        assert result is True
        game_checker.check_active_games.assert_called_once()
        screenshot_controller.take_screenshot.assert_called_once()

    def test_refresh_display_no_active_games_skips_update(self):
        """Test that display update is skipped when no active games"""
        # Arrange
        config = {"max_retries": 3, "retry_delay": 1}
        game_checker = Mock()
        game_checker.check_active_games.return_value = False  # No active games
        screenshot_controller = Mock()

        controller = RefreshController(config, game_checker, screenshot_controller)

        # Act
        result = controller.refresh_display(force_update=False)

        # Assert
        assert result is True  # Success, but skipped
        game_checker.check_active_games.assert_called_once()
        screenshot_controller.take_screenshot.assert_not_called()  # Skipped

    @patch("src.display.refresh_controller.time.sleep")
    def test_refresh_display_retries_screenshot(self, mock_sleep):
        """Test that screenshot is retried on failure"""
        # Arrange
        config = {"max_retries": 3, "retry_delay": 2}
        game_checker = Mock()
        screenshot_controller = Mock()
        # First two attempts fail, third succeeds
        screenshot_controller.take_screenshot.side_effect = [False, False, True]
        screenshot_controller.process_image.return_value = Mock()
        screenshot_controller.update_display.return_value = True

        controller = RefreshController(config, game_checker, screenshot_controller)

        # Act
        result = controller.refresh_display(force_update=True)

        # Assert
        assert result is True
        assert screenshot_controller.take_screenshot.call_count == 3
        assert mock_sleep.call_count == 2  # Slept between retries
        mock_sleep.assert_called_with(2)  # retry_delay

    @patch("src.display.refresh_controller.time.sleep")
    def test_refresh_display_screenshot_fails_all_retries(self, mock_sleep):
        """Test that refresh fails if screenshot fails all retries"""
        # Arrange
        config = {"max_retries": 3, "retry_delay": 1}
        game_checker = Mock()
        screenshot_controller = Mock()
        screenshot_controller.take_screenshot.return_value = False  # Always fails

        controller = RefreshController(config, game_checker, screenshot_controller)

        # Act
        result = controller.refresh_display(force_update=True)

        # Assert
        assert result is False
        assert screenshot_controller.take_screenshot.call_count == 3
        screenshot_controller.process_image.assert_not_called()

    def test_refresh_display_image_processing_fails(self):
        """Test that refresh fails if image processing fails"""
        # Arrange
        config = {"max_retries": 3, "retry_delay": 1}
        game_checker = Mock()
        screenshot_controller = Mock()
        screenshot_controller.take_screenshot.return_value = True
        screenshot_controller.process_image.return_value = None  # Processing failed

        controller = RefreshController(config, game_checker, screenshot_controller)

        # Act
        result = controller.refresh_display(force_update=True)

        # Assert
        assert result is False
        screenshot_controller.update_display.assert_not_called()

    def test_refresh_display_update_display_fails(self):
        """Test that refresh fails if display update fails"""
        # Arrange
        config = {"max_retries": 3, "retry_delay": 1}
        game_checker = Mock()
        screenshot_controller = Mock()
        screenshot_controller.take_screenshot.return_value = True
        screenshot_controller.process_image.return_value = Mock()
        screenshot_controller.update_display.return_value = False  # Update failed

        controller = RefreshController(config, game_checker, screenshot_controller)

        # Act
        result = controller.refresh_display(force_update=True)

        # Assert
        assert result is False


@pytest.mark.unit
class TestRunContinuous:
    """Tests for run_continuous method - basic scenarios"""

    @patch("src.display.refresh_controller.time.sleep")
    @patch("src.display.refresh_controller.datetime")
    @patch.object(RefreshController, "_wait_for_memory_on_startup")
    @patch.object(RefreshController, "refresh_display")
    def test_run_continuous_new_game_day_forces_update(
        self, mock_refresh, mock_wait_memory, mock_datetime, mock_sleep
    ):
        """Test that a new game day forces a display update"""
        # Arrange
        config = {"refresh_interval": 60, "retry_delay": 5}
        game_checker = Mock()
        game_checker.get_game_state.return_value = {
            "has_active_games": False,
            "has_any_games": True,
            "scheduled_games": [{"status": "7:05 PM ET"}],
            "final_games": [],
        }
        screenshot_controller = Mock()

        controller = RefreshController(config, game_checker, screenshot_controller)

        # Setup datetime mock to return specific dates
        mock_now = Mock()
        mock_now.strftime.side_effect = lambda fmt: (
            "2024-09-15" if fmt == "%Y-%m-%d" else "12"
        )
        mock_now.hour = 12
        mock_datetime.now.return_value = mock_now

        wait_callback = Mock(return_value=True)
        mock_refresh.return_value = True

        # Make sleep raise KeyboardInterrupt after first iteration
        mock_sleep.side_effect = KeyboardInterrupt()

        # Act
        controller.run_continuous(wait_callback)

        # Assert
        # Should have called refresh_display with force_update=True for new day
        assert mock_refresh.call_count >= 1
        # First call should be with force_update=True
        first_call = mock_refresh.call_args_list[0]
        assert first_call[1].get("force_update") is True

    @patch("src.display.refresh_controller.time.sleep")
    @patch("src.display.refresh_controller.datetime")
    @patch.object(RefreshController, "_wait_for_memory_on_startup")
    @patch.object(RefreshController, "refresh_display")
    def test_run_continuous_server_not_ready(
        self, mock_refresh, mock_wait_memory, mock_datetime, mock_sleep
    ):
        """Test that run_continuous exits if server is not ready"""
        # Arrange
        config = {"refresh_interval": 60}
        controller = RefreshController(config, Mock(), Mock())

        wait_callback = Mock(return_value=False)  # Server not ready

        # Act
        result = controller.run_continuous(wait_callback)

        # Assert
        assert result is False
        mock_wait_memory.assert_not_called()
        mock_refresh.assert_not_called()

    @patch("src.display.refresh_controller.time.sleep")
    @patch("src.display.refresh_controller.datetime")
    @patch.object(RefreshController, "_wait_for_memory_on_startup")
    @patch.object(RefreshController, "refresh_display")
    def test_run_continuous_handles_keyboard_interrupt(
        self, mock_refresh, mock_wait_memory, mock_datetime, mock_sleep
    ):
        """Test that KeyboardInterrupt is handled gracefully"""
        # Arrange
        config = {"refresh_interval": 60}
        game_checker = Mock()
        game_checker.get_game_state.return_value = {
            "has_active_games": False,
            "has_any_games": False,
        }
        controller = RefreshController(config, game_checker, Mock())

        mock_now = Mock()
        mock_now.strftime.return_value = "2024-09-15"
        mock_now.hour = 12
        mock_datetime.now.return_value = mock_now

        wait_callback = Mock(return_value=True)

        # Raise KeyboardInterrupt on first iteration
        mock_sleep.side_effect = KeyboardInterrupt()

        # Act - Should not raise exception
        controller.run_continuous(wait_callback)

        # Assert - Should have exited cleanly
        assert mock_sleep.call_count >= 1

    @patch("src.display.refresh_controller.time.sleep")
    @patch("src.display.refresh_controller.datetime")
    @patch("src.display.refresh_controller.log_resource_snapshot")
    @patch.object(RefreshController, "_wait_for_memory_on_startup")
    @patch.object(RefreshController, "refresh_display")
    def test_run_continuous_handles_network_error(
        self,
        mock_refresh,
        mock_wait_memory,
        mock_log_resource,
        mock_datetime,
        mock_sleep,
    ):
        """Test that network errors are handled with backoff"""
        # Arrange
        import requests

        config = {"refresh_interval": 60, "retry_delay": 5}
        game_checker = Mock()
        # First call raises network error, second raises KeyboardInterrupt to exit
        game_checker.get_game_state.side_effect = [
            requests.exceptions.RequestException("Network error"),
            KeyboardInterrupt(),
        ]

        controller = RefreshController(config, game_checker, Mock())

        mock_now = Mock()
        mock_now.strftime.return_value = "2024-09-15"
        mock_now.hour = 12
        mock_datetime.now.return_value = mock_now

        wait_callback = Mock(return_value=True)

        # Act
        controller.run_continuous(wait_callback)

        # Assert
        # Should have logged the network error
        assert mock_log_resource.called
        # Should have slept with backoff
        assert mock_sleep.called

    @patch("src.display.refresh_controller.time.sleep")
    @patch("src.display.refresh_controller.datetime")
    @patch("src.display.refresh_controller.log_resource_snapshot")
    @patch.object(RefreshController, "_wait_for_memory_on_startup")
    @patch.object(RefreshController, "refresh_display")
    def test_run_continuous_handles_memory_error(
        self,
        mock_refresh,
        mock_wait_memory,
        mock_log_resource,
        mock_datetime,
        mock_sleep,
    ):
        """Test that memory errors are logged with resource snapshot"""
        # Arrange
        config = {"refresh_interval": 60, "retry_delay": 5}
        game_checker = Mock()
        # First call raises MemoryError, second raises KeyboardInterrupt to exit
        game_checker.get_game_state.side_effect = [
            MemoryError("Out of memory"),
            KeyboardInterrupt(),
        ]

        controller = RefreshController(config, game_checker, Mock())

        mock_now = Mock()
        mock_now.strftime.return_value = "2024-09-15"
        mock_now.hour = 12
        mock_datetime.now.return_value = mock_now

        wait_callback = Mock(return_value=True)

        # Act
        controller.run_continuous(wait_callback)

        # Assert
        # Should have logged the memory error with resource snapshot
        assert mock_log_resource.called
        # Verify it was called with MEMORY_ERROR tag
        call_args = [call[0][1] for call in mock_log_resource.call_args_list]
        assert "MEMORY_ERROR" in call_args
