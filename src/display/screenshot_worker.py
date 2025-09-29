#!/usr/bin/env python3
"""
Subprocess worker for taking screenshots in isolation.
This runs in a separate process that can be killed if it hangs.
"""

import json
import logging
import os
import signal
import sys
import time

# Add parent directory to path so we can import display module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging to be visible - simple format since parent adds prefix
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",  # Simple format - parent adds [WORKER] prefix
    force=True,
)
logger = logging.getLogger(__name__)

# Immediate startup message
logger.info("Worker process started")


def timeout_handler(signum, frame):
    """Handle timeout by exiting cleanly."""
    logger.error("Worker process timeout - exiting")
    # Don't force kill browsers here - let the parent process handle cleanup
    # This prevents zombie processes from accumulating
    sys.exit(1)


def take_screenshot(config_json):
    """Take a screenshot in an isolated process."""
    logger.info("Parsing config")
    config = json.loads(config_json)
    logger.info(f"Config parsed - URL: {config.get('web_server_url')}")

    # Set up internal timeout (145 seconds - less than parent's 150s)
    # This ensures clean exit before parent kills us
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(145)
    logger.info("Timeout alarm set for 145 seconds")

    try:
        logger.info("Importing playwright")
        from playwright.sync_api import sync_playwright

        # Import BrowserCleanup from the display module
        logger.info("Importing browser cleanup")
        from display.browser_cleanup import BrowserCleanup

        logger.info("Starting Playwright context")
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

            logger.info("Launching browser")
            browser = p.chromium.launch(headless=True, args=browser_args)
            logger.info("Browser launched")

            logger.info("Creating page")
            page = browser.new_page(
                viewport={
                    "width": config["display_width"],
                    "height": config["display_height"],
                },
                device_scale_factor=config.get("screenshot_scale", 1),
                color_scheme="light",
            )

            # Set page timeout (longer for Pi Zero)
            page.set_default_timeout(30000)

            # Load page with generous timeout for slow Pi Zero
            logger.info(f"Loading page - {config['web_server_url']}")
            page.goto(
                config["web_server_url"], wait_until="domcontentloaded", timeout=60000
            )
            logger.info("Page loaded")

            # Wait for content
            try:
                page.wait_for_selector(
                    ".game-card, .game-pill, #games > div", timeout=20000
                )
                logger.info("Game content detected")
            except Exception:
                logger.warning("No game content found - waiting for JS")
                page.wait_for_timeout(10000)

            # Wait for screensaver background image to load if present
            try:
                screensaver_container = page.query_selector(".screensaver-container")
                if screensaver_container:
                    logger.info("Screensaver detected - waiting for background image")
                    # Wait for the image to be loaded (signaled by data attribute)
                    page.wait_for_selector(
                        ".screensaver-container[data-image-loaded='true']",
                        timeout=15000,
                    )
                    logger.info("Screensaver background image loaded")
                    # Extra wait to ensure image is fully rendered
                    page.wait_for_timeout(1000)
            except Exception as e:
                logger.warning(f"Screensaver image wait timeout: {e}")

            # Take screenshot
            page.screenshot(path=config["screenshot_path"], full_page=False)

            # Cleanup
            page.close()
            browser.close()

            # Wait longer for browser to fully close on Pi Zero
            time.sleep(2)

            # Make sure playwright is cleaned up
            p.stop()

            # Cancel the timeout alarm since we succeeded
            signal.alarm(0)
            logger.info(f"Screenshot saved - {config['screenshot_path']}")
            return 0

    except Exception as e:
        logger.error(f"Screenshot failed: {e}")
        # Cancel the timeout alarm
        signal.alarm(0)
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
