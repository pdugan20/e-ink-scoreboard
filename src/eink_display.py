#!/usr/bin/env python3
"""
Direct eink display controller for E-Ink Scoreboard
Works on both Mac (for testing) and Raspberry Pi (with actual eink display)
"""

import json
import logging
import os
import sys
import time

import requests

# Try to import systemd notifier for watchdog
try:
    from systemd import daemon

    SYSTEMD_AVAILABLE = True
except ImportError:
    SYSTEMD_AVAILABLE = False

# Import our modular display components
from display.game_checker import GameChecker
from display.refresh_controller import RefreshController
from display.screenshot_controller import ScreenshotController
from utils.logging_config import setup_logging

logger = logging.getLogger(__name__)

# Default configuration (will be overridden by config file)
CONFIG = {
    "web_server_url": "http://localhost:5001/display",
    "screenshot_path": "/tmp/sports_display.png",
    "display_width": 800,
    "display_height": 480,
    "screenshot_scale": 1,
    "refresh_interval": 300,
    "apply_dithering": False,
    "dither_saturation": 0.8,
    "max_retries": 3,
    "retry_delay": 5,
}


class EinkDisplayController:
    def __init__(self, config=None):
        self.config = config or CONFIG

        # Initialize modular components
        self.game_checker = GameChecker(self.config["web_server_url"])
        self.screenshot_controller = ScreenshotController(self.config)
        self.refresh_controller = RefreshController(
            self.config, self.game_checker, self.screenshot_controller
        )

    def wait_for_server(self, timeout=60):
        """Wait for the web server to be available"""
        logger.info(f"Waiting for server at {self.config['web_server_url']}")
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = requests.get(self.config["web_server_url"], timeout=5)
                if response.status_code == 200:
                    logger.info("Server is ready")
                    return True
            except requests.RequestException:
                pass

            time.sleep(2)

        logger.error(f"Server not available after {timeout} seconds")
        return False

    def refresh_display(self, force_update=False):
        """Complete refresh cycle: screenshot -> process -> display"""
        return self.refresh_controller.refresh_display(force_update)

    def run_continuous(self):
        """Run continuous refresh loop with smart game detection and screensaver refresh"""
        # Notify systemd we're ready
        if SYSTEMD_AVAILABLE:
            daemon.notify("READY=1")
            logger.info("Systemd watchdog enabled")

        # Start a thread to send watchdog heartbeats
        if SYSTEMD_AVAILABLE:
            import threading

            def watchdog_heartbeat():
                while True:
                    daemon.notify("WATCHDOG=1")
                    time.sleep(30)  # Send heartbeat every 30 seconds

            watchdog_thread = threading.Thread(target=watchdog_heartbeat, daemon=True)
            watchdog_thread.start()
            logger.info("Watchdog heartbeat thread started")

        try:
            return self.refresh_controller.run_continuous(self.wait_for_server)
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up resources...")
        if hasattr(self, "game_checker"):
            self.game_checker.cleanup()
        if hasattr(self, "screenshot_controller"):
            # Kill any remaining browser processes
            if hasattr(self.screenshot_controller, "_kill_hanging_browsers"):
                self.screenshot_controller._kill_hanging_browsers()


def load_config(config_file="eink_config.json"):
    """Load configuration from file if it exists"""
    if os.path.exists(config_file):
        try:
            with open(config_file) as f:
                user_config = json.load(f)
                config = CONFIG.copy()
                config.update(user_config)
                return config
        except Exception as e:
            logger.warning(f"Failed to load config file: {e}")
    return CONFIG


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="E-Ink Scoreboard Display Controller")
    parser.add_argument(
        "--once", action="store_true", help="Update display once and exit"
    )
    parser.add_argument(
        "--force", action="store_true", help="Force update (bypass active game check)"
    )
    parser.add_argument(
        "--config", default="eink_config.json", help="Configuration file path"
    )
    parser.add_argument("--interval", type=int, help="Refresh interval in seconds")
    parser.add_argument("--url", help="Web server URL")
    parser.add_argument(
        "--dithering", action="store_true", help="Apply e-ink dithering for testing"
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Setup comprehensive logging first
    setup_logging(config)

    # Override with command line arguments
    if args.interval:
        config["refresh_interval"] = args.interval
    if args.url:
        config["web_server_url"] = args.url
    if args.dithering:
        config["apply_dithering"] = True
        logger.info("Dithering enabled via command line flag")

    # Create controller
    controller = EinkDisplayController(config)

    if args.once:
        # Single update - respect active game logic unless --force is specified
        if not controller.wait_for_server():
            sys.exit(1)

        force_update = args.force
        success = controller.refresh_display(force_update=force_update)
        sys.exit(0 if success else 1)
    else:
        # Continuous mode
        controller.run_continuous()


if __name__ == "__main__":
    main()
