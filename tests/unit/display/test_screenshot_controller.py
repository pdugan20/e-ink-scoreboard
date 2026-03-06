"""
Unit tests for ScreenshotController class.

Tests initialization, platform detection, and process management.
Complex Playwright browser automation is tested in integration suite.
"""

import sys
from unittest.mock import Mock, mock_open, patch

import pytest

# Create proper mock modules to avoid pytest plugin discovery issues
config_mock = type(sys)("config")
config_mock.memory_config = type(sys)("memory_config")
config_mock.memory_config.MEMORY_MINIMUM_MB = 100
config_mock.memory_config.MEMORY_RECOMMENDED_MB = 200
config_mock.memory_config.BROWSER_JS_HEAP_MB = 50

utils_mock = type(sys)("utils")
utils_mock.logging_config = type(sys)("logging_config")
utils_mock.logging_config.log_before_screenshot = Mock()
utils_mock.logging_config.log_after_screenshot = Mock()
utils_mock.logging_config.log_browser_cleanup = Mock()

display_mock = type(sys)("display")
display_mock.browser_cleanup = type(sys)("browser_cleanup")
display_mock.browser_cleanup.BrowserCleanup = Mock()

sys.modules["config"] = config_mock
sys.modules["config.memory_config"] = config_mock.memory_config
sys.modules["utils"] = utils_mock
sys.modules["utils.logging_config"] = utils_mock.logging_config
sys.modules["display"] = display_mock
sys.modules["display.browser_cleanup"] = display_mock.browser_cleanup

from src.display.screenshot_controller import ScreenshotController  # noqa: E402


@pytest.mark.unit
class TestScreenshotControllerInit:
    """Tests for ScreenshotController initialization"""

    @patch("src.display.screenshot_controller.platform.system")
    def test_init_on_mac(self, mock_platform):
        """Test initialization on macOS"""
        # Arrange
        mock_platform.return_value = "Darwin"
        config = {"web_server_url": "http://localhost:5000/display"}

        # Act
        controller = ScreenshotController(config, test_mode=True)

        # Assert
        assert controller.config == config
        assert controller.test_mode is True
        assert controller.is_mac is True
        assert controller.is_pi is False

    @patch("src.display.screenshot_controller.platform.system")
    @patch.object(ScreenshotController, "_is_raspberry_pi")
    def test_init_on_linux_not_pi(self, mock_is_pi, mock_platform):
        """Test initialization on Linux (not Raspberry Pi)"""
        # Arrange
        mock_platform.return_value = "Linux"
        mock_is_pi.return_value = False
        config = {"web_server_url": "http://localhost:5000/display"}

        # Act
        controller = ScreenshotController(config)

        # Assert
        assert controller.is_mac is False
        assert controller.is_pi is False

    @patch("src.display.screenshot_controller.platform.system")
    @patch.object(ScreenshotController, "_is_raspberry_pi")
    def test_init_on_raspberry_pi(self, mock_is_pi, mock_platform):
        """Test initialization on Raspberry Pi"""
        # Arrange
        mock_platform.return_value = "Linux"
        mock_is_pi.return_value = True
        config = {"web_server_url": "http://localhost:5000/display"}

        # Act
        controller = ScreenshotController(config)

        # Assert
        assert controller.is_mac is False
        assert controller.is_pi is True


@pytest.mark.unit
class TestIsRaspberryPi:
    """Tests for _is_raspberry_pi method"""

    @patch("src.display.screenshot_controller.platform.system")
    def test_is_raspberry_pi_true_with_raspberry_pi_string(self, mock_platform):
        """Test detection when cpuinfo contains 'Raspberry Pi'"""
        # Arrange
        mock_platform.return_value = "Linux"
        cpuinfo_content = """
        processor	: 0
        model name	: ARMv7 Processor rev 4 (v7l)
        Hardware	: BCM2835
        Revision	: a02082
        Serial		: 00000000abc12345
        Model		: Raspberry Pi 3 Model B Rev 1.2
        """
        config = {"web_server_url": "http://localhost:5000/display"}

        with patch("builtins.open", mock_open(read_data=cpuinfo_content)):
            # Act
            controller = ScreenshotController(config)

        # Assert - Check that it was detected as Raspberry Pi during init
        assert controller.is_pi is True

    @patch("src.display.screenshot_controller.platform.system")
    def test_is_raspberry_pi_true_with_bcm_string(self, mock_platform):
        """Test detection when cpuinfo contains 'BCM'"""
        # Arrange
        mock_platform.return_value = "Linux"
        cpuinfo_content = """
        processor	: 0
        Hardware	: BCM2835
        """
        config = {"web_server_url": "http://localhost:5000/display"}

        with patch("builtins.open", mock_open(read_data=cpuinfo_content)):
            # Act
            controller = ScreenshotController(config)

        # Assert - Check that it was detected as Raspberry Pi during init
        assert controller.is_pi is True

    @patch("src.display.screenshot_controller.platform.system")
    def test_is_raspberry_pi_false_on_regular_linux(self, mock_platform):
        """Test detection returns False on regular Linux"""
        # Arrange
        mock_platform.return_value = "Linux"
        cpuinfo_content = """
        processor	: 0
        vendor_id	: GenuineIntel
        model name	: Intel(R) Core(TM) i5-8250U CPU @ 1.60GHz
        """
        config = {"web_server_url": "http://localhost:5000/display"}

        with patch("builtins.open", mock_open(read_data=cpuinfo_content)):
            # Act
            controller = ScreenshotController(config)

        # Assert
        assert controller._is_raspberry_pi() is False

    @patch("src.display.screenshot_controller.platform.system")
    def test_is_raspberry_pi_false_when_file_not_found(self, mock_platform):
        """Test detection returns False when /proc/cpuinfo doesn't exist"""
        # Arrange
        mock_platform.return_value = "Linux"
        config = {"web_server_url": "http://localhost:5000/display"}

        with patch("builtins.open", side_effect=FileNotFoundError()):
            # Act
            controller = ScreenshotController(config)

        # Assert
        assert controller._is_raspberry_pi() is False


@pytest.mark.unit
class TestUpdateDisplaySubprocess:
    """Tests for _update_display_subprocess method"""

    @patch("src.display.screenshot_controller.platform.system")
    @patch.object(ScreenshotController, "_is_raspberry_pi")
    def test_update_display_routes_to_subprocess_on_pi(self, mock_is_pi, mock_platform):
        """Test that update_display delegates to subprocess on Pi"""
        # Arrange
        mock_platform.return_value = "Linux"
        mock_is_pi.return_value = True
        config = {
            "web_server_url": "http://localhost:5000/display",
            "screenshot_path": "/tmp/test.png",
            "apply_dithering": False,
            "dither_saturation": 0.8,
        }
        controller = ScreenshotController(config)
        mock_img = Mock()

        with patch.object(
            controller, "_update_display_subprocess", return_value=True
        ) as mock_subprocess:
            # Act
            result = controller.update_display(mock_img)

        # Assert
        assert result is True
        mock_subprocess.assert_called_once_with(mock_img)

    @patch("src.display.screenshot_controller.platform.system")
    def test_update_display_saves_file_on_mac(self, mock_platform):
        """Test that update_display saves file on Mac"""
        # Arrange
        mock_platform.return_value = "Darwin"
        config = {"web_server_url": "http://localhost:5000/display"}
        controller = ScreenshotController(config, test_mode=True)
        mock_img = Mock()

        # Act
        result = controller.update_display(mock_img)

        # Assert
        assert result is True
        mock_img.save.assert_called_once_with("test_display_output.png")


@pytest.mark.unit
class TestKillHangingBrowsers:
    """Tests for _kill_hanging_browsers method"""

    @patch("src.display.screenshot_controller.platform.system")
    @patch("src.display.screenshot_controller.psutil.process_iter")
    @patch("src.display.screenshot_controller.time.sleep")
    def test_kill_hanging_browsers_finds_and_kills_chromium(
        self, mock_sleep, mock_process_iter, mock_platform
    ):
        """Test that hanging Chromium processes are identified and killed"""
        # Arrange
        mock_platform.return_value = "Darwin"
        config = {"web_server_url": "http://localhost:5000/display"}
        controller = ScreenshotController(config, test_mode=True)

        mock_proc = Mock()
        mock_proc.info = {
            "pid": 12345,
            "name": "chromium",
            "cmdline": ["chromium", "--headless", "--disable-gpu"],
        }
        mock_proc.is_running.return_value = False
        mock_process_iter.return_value = [mock_proc]

        # Act
        controller._kill_hanging_browsers()

        # Assert
        mock_proc.terminate.assert_called_once()

    @patch("src.display.screenshot_controller.platform.system")
    @patch("src.display.screenshot_controller.psutil.process_iter")
    @patch("src.display.screenshot_controller.time.sleep")
    def test_kill_hanging_browsers_force_kills_stubborn_process(
        self, mock_sleep, mock_process_iter, mock_platform
    ):
        """Test that stubborn processes are force killed"""
        # Arrange
        mock_platform.return_value = "Darwin"
        config = {"web_server_url": "http://localhost:5000/display"}
        controller = ScreenshotController(config, test_mode=True)

        mock_proc = Mock()
        mock_proc.info = {
            "pid": 12345,
            "name": "chrome",
            "cmdline": ["chrome", "--headless"],
        }
        mock_proc.is_running.return_value = True  # Still running after terminate
        mock_process_iter.return_value = [mock_proc]

        # Act
        controller._kill_hanging_browsers()

        # Assert
        mock_proc.terminate.assert_called_once()
        mock_proc.kill.assert_called_once()  # Force kill called

    @patch("src.display.screenshot_controller.platform.system")
    @patch("src.display.screenshot_controller.psutil.process_iter")
    def test_kill_hanging_browsers_ignores_non_browser_processes(
        self, mock_process_iter, mock_platform
    ):
        """Test that non-browser processes are ignored"""
        # Arrange
        mock_platform.return_value = "Darwin"
        config = {"web_server_url": "http://localhost:5000/display"}
        controller = ScreenshotController(config, test_mode=True)

        mock_proc = Mock()
        mock_proc.info = {
            "pid": 12345,
            "name": "python",
            "cmdline": ["python", "script.py"],
        }
        mock_process_iter.return_value = [mock_proc]

        # Act
        controller._kill_hanging_browsers()

        # Assert
        mock_proc.terminate.assert_not_called()

    @patch("src.display.screenshot_controller.platform.system")
    @patch("src.display.screenshot_controller.psutil.process_iter")
    def test_kill_hanging_browsers_handles_access_denied(
        self, mock_process_iter, mock_platform
    ):
        """Test that AccessDenied errors are handled gracefully"""
        # Arrange
        import psutil

        mock_platform.return_value = "Darwin"
        config = {"web_server_url": "http://localhost:5000/display"}
        controller = ScreenshotController(config, test_mode=True)

        mock_proc = Mock()
        mock_proc.info = {
            "pid": 12345,
            "name": "chromium",
            "cmdline": ["chromium", "--headless"],
        }
        mock_proc.terminate.side_effect = psutil.AccessDenied()
        mock_process_iter.return_value = [mock_proc]

        # Act - Should not raise exception
        controller._kill_hanging_browsers()

        # Assert
        mock_proc.terminate.assert_called_once()

    @patch("src.display.screenshot_controller.platform.system")
    @patch("src.display.screenshot_controller.psutil.process_iter")
    def test_kill_hanging_browsers_handles_no_such_process(
        self, mock_process_iter, mock_platform
    ):
        """Test that NoSuchProcess errors during iteration are handled gracefully"""
        # Arrange
        import psutil

        mock_platform.return_value = "Darwin"
        config = {"web_server_url": "http://localhost:5000/display"}
        controller = ScreenshotController(config, test_mode=True)

        # Create a process that raises NoSuchProcess when accessing info
        mock_proc = Mock()
        mock_proc.info = Mock(side_effect=psutil.NoSuchProcess(12345))

        mock_process_iter.return_value = [mock_proc]

        # Act - Should not raise exception
        controller._kill_hanging_browsers()

        # Assert - Process iteration should have been attempted
        mock_process_iter.assert_called_once()

    @patch("src.display.screenshot_controller.platform.system")
    @patch("src.display.screenshot_controller.psutil.process_iter")
    def test_kill_hanging_browsers_handles_general_exception(
        self, mock_process_iter, mock_platform
    ):
        """Test that general exceptions during cleanup are handled"""
        # Arrange
        mock_platform.return_value = "Darwin"
        config = {"web_server_url": "http://localhost:5000/display"}
        controller = ScreenshotController(config, test_mode=True)

        mock_process_iter.side_effect = Exception("Unexpected error")

        # Act - Should not raise exception
        controller._kill_hanging_browsers()

        # Assert - Should have tried to get processes
        mock_process_iter.assert_called_once()
