#!/usr/bin/env python3
"""
Subprocess worker for taking screenshots in isolation.
This runs in a separate process that can be killed if it hangs.
"""

import json
import logging
import os
import sys
import time

# Add parent directory to path so we can import display module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def take_screenshot(config_json):
    """Take a screenshot in an isolated process."""
    config = json.loads(config_json)

    try:
        from playwright.sync_api import sync_playwright

        # Import BrowserCleanup from the display module
        from display.browser_cleanup import BrowserCleanup

        with sync_playwright() as p:
            browser_args = [
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--disable-extensions",
                "--disable-plugins",
                "--disable-translate",
                "--disable-webgl",
                f"--js-flags=--max-old-space-size={config.get('browser_js_heap_mb', 96)}",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--single-process",
                "--disable-features=site-per-process",
                "--memory-pressure-off",
                "--max_old_space_size=96",
                "--aggressive-cache-discard",
                "--disable-features=RendererCodeIntegrity",
            ]

            browser = p.chromium.launch(headless=True, args=browser_args)

            page = browser.new_page(
                viewport={
                    "width": config["display_width"],
                    "height": config["display_height"],
                },
                device_scale_factor=config.get("screenshot_scale", 1),
                color_scheme="light",
            )

            # Set page timeout
            page.set_default_timeout(20000)

            # Load page
            page.goto(
                config["web_server_url"], wait_until="domcontentloaded", timeout=30000
            )

            # Wait for content
            try:
                page.wait_for_selector(
                    ".game-card, .game-pill, #games > div", timeout=15000
                )
                logger.info("Game content detected")
            except Exception:
                logger.warning("No game content found, waiting for JS...")
                page.wait_for_timeout(8000)

            # Take screenshot
            page.screenshot(path=config["screenshot_path"], full_page=False)

            # Cleanup
            page.close()
            browser.close()

            # Force cleanup browser processes
            time.sleep(1)
            BrowserCleanup.force_kill_all_browsers()

            logger.info(f"Screenshot saved to {config['screenshot_path']}")
            return 0

    except Exception as e:
        logger.error(f"Screenshot failed: {e}")
        # Try to cleanup on error
        try:
            BrowserCleanup.force_kill_all_browsers()
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: screenshot_worker.py <config_json>", file=sys.stderr)
        sys.exit(1)

    sys.exit(take_screenshot(sys.argv[1]))
