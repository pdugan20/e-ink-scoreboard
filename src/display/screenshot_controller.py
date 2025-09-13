"""
Screenshot and image processing logic for e-ink display.
"""

import logging
import os
import platform
import subprocess
import time
from contextlib import contextmanager

import psutil
from PIL import Image

from utils.logging_config import (
    log_after_screenshot,
    log_before_screenshot,
    log_browser_cleanup,
)

logger = logging.getLogger(__name__)


class ScreenshotController:
    """Handles taking screenshots and processing images for e-ink display."""

    def __init__(self, config):
        self.config = config
        self.is_mac = platform.system() == "Darwin"
        self.is_pi = platform.system() == "Linux" and self._is_raspberry_pi()

        if self.is_pi:
            self.inky = self._initialize_inky_display()
        else:
            self.inky = None
            logger.info("Running in test mode (no physical eink display)")

    def _is_raspberry_pi(self):
        """Check if running on Raspberry Pi"""
        try:
            with open("/proc/cpuinfo") as f:
                cpuinfo = f.read()
                return "Raspberry Pi" in cpuinfo or "BCM" in cpuinfo
        except FileNotFoundError:
            return False

    def _initialize_inky_display(self):
        """Initialize the Inky e-ink display"""
        try:
            # Try auto-detection first
            from inky.auto import auto

            inky = auto()
            logger.info(f"Auto-detected Inky display: {inky.width}x{inky.height}")
            return inky
        except ImportError as e:
            logger.error(f"Inky library not found: {e}. Install with: pip install inky")
            raise
        except Exception as e:
            # Fallback to Inky Impression 7.3" if auto-detection fails
            logger.warning(
                f"Auto-detection failed ({e}), trying Inky Impression 7.3..."
            )
            try:
                from inky import Inky_Impressions_7

                inky = Inky_Impressions_7()
                logger.info(
                    f"Initialized Inky Impression 7.3: {inky.width}x{inky.height}"
                )
                return inky
            except Exception as e2:
                logger.error(f"Failed to initialize Inky display: {e2}")
                raise

    def _kill_hanging_browsers(self):
        """Kill any hanging browser processes to prevent resource leaks."""
        killed_processes = []
        try:
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    name = proc.info["name"].lower()
                    cmdline = " ".join(proc.info["cmdline"] or []).lower()

                    # Look for browser processes that might be hanging
                    is_browser = any(
                        browser in name
                        for browser in ["chromium", "chrome", "playwright"]
                    )
                    has_headless = "headless" in cmdline
                    has_display_url = (
                        self.config["web_server_url"].split("/")[-1] in cmdline
                    )

                    if is_browser and (has_headless or has_display_url):
                        try:
                            proc.terminate()
                            killed_processes.append(
                                {"pid": proc.info["pid"], "name": proc.info["name"]}
                            )
                            logger.info(
                                f"Terminated hanging browser process: {proc.info['pid']} ({proc.info['name']})"
                            )

                            # Give process time to terminate gracefully
                            time.sleep(1)

                            # Force kill if still running
                            if proc.is_running():
                                proc.kill()
                                logger.warning(
                                    f"Force killed stubborn browser process: {proc.info['pid']}"
                                )

                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass  # Process already gone or can't access
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if killed_processes:
                log_browser_cleanup(logger, {"killed_processes": killed_processes})

        except Exception as e:
            logger.warning(f"Error during browser cleanup: {e}")

    @contextmanager
    def _browser_process_manager(self):
        """Context manager to ensure browser processes are cleaned up."""
        initial_browsers = self._count_browser_processes()
        log_before_screenshot(logger)

        try:
            yield
        finally:
            final_browsers = self._count_browser_processes()

            # If we have more browser processes than we started with, try cleanup
            if final_browsers > initial_browsers:
                logger.warning(
                    f"Browser process count increased from {initial_browsers} to {final_browsers}"
                )
                self._kill_hanging_browsers()
                time.sleep(2)  # Give cleanup time to work
                after_cleanup = self._count_browser_processes()
                logger.info(f"After cleanup: {after_cleanup} browser processes")

    def _count_browser_processes(self):
        """Count current browser processes."""
        try:
            count = 0
            for proc in psutil.process_iter(["name"]):
                try:
                    name = proc.info["name"].lower()
                    if any(
                        browser in name
                        for browser in ["chromium", "chrome", "playwright"]
                    ):
                        count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return count
        except Exception:
            return 0

    def take_screenshot(self):
        """Take screenshot using available method with browser process management."""
        with self._browser_process_manager():
            # Try Playwright first (works on both Mac and Pi)
            try:
                success = self._screenshot_playwright()
                log_after_screenshot(logger, success)
                return success
            except ImportError:
                logger.info("Playwright not available, falling back to system Chromium")
                if self.is_mac:
                    success = self._screenshot_mac_chromium()
                else:
                    success = self._screenshot_linux()
                log_after_screenshot(logger, success)
                return success

    def _screenshot_playwright(self):
        """Take screenshot using Playwright (works on both Mac and Pi)"""
        from playwright.sync_api import sync_playwright

        browser = None
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"]
                )

                # Get scale factor from config
                scale_factor = self.config.get("screenshot_scale", 1)

                page = browser.new_page(
                    viewport={
                        "width": self.config["display_width"],
                        "height": self.config["display_height"],
                    },
                    device_scale_factor=scale_factor,  # High DPI rendering
                )

                logger.info(
                    f"Taking screenshot with Playwright ({scale_factor}x DPI rendering)..."
                )

                # Increase timeout for slower Pi and RSS feed loading
                page.set_default_timeout(90000)  # 90 seconds

                try:
                    page.goto(
                        self.config["web_server_url"],
                        wait_until="networkidle",
                        timeout=90000,
                    )
                except Exception as e:
                    # Fallback to domcontentloaded if networkidle times out
                    logger.warning(
                        f"Network idle timeout, trying domcontentloaded: {e}"
                    )
                    page.goto(
                        self.config["web_server_url"],
                        wait_until="domcontentloaded",
                        timeout=60000,
                    )

                # Wait for images to load (especially screensaver images)
                page.wait_for_timeout(8000)

                page.screenshot(path=self.config["screenshot_path"], full_page=False)

                # Ensure page and browser are properly closed
                page.close()
                browser.close()
                browser = None

                logger.info(f"Screenshot saved to {self.config['screenshot_path']}")
                return True

        except Exception as e:
            logger.error(f"Playwright screenshot failed: {e}")
            # Ensure browser is closed even on error
            if browser:
                try:
                    browser.close()
                except Exception:
                    pass
            return False

    def _screenshot_mac_chromium(self):
        """Take screenshot on Mac using Chrome headless fallback"""
        try:
            # Fallback to Chrome headless
            chrome_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chromium.app/Contents/MacOS/Chromium",
                "google-chrome",
                "chromium-browser",
            ]

            chrome_cmd = None
            for path in chrome_paths:
                if (
                    os.path.exists(path)
                    or subprocess.run(["which", path], capture_output=True).returncode
                    == 0
                ):
                    chrome_cmd = path
                    break

            if not chrome_cmd:
                raise RuntimeError("Neither Playwright nor Chrome/Chromium found")

            cmd = [
                chrome_cmd,
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                "--disable-web-security",
                "--allow-running-insecure-content",
                f"--window-size={self.config['display_width']},{self.config['display_height']}",
                f"--screenshot={self.config['screenshot_path']}",
                "--force-device-scale-factor=1",
                "--hide-scrollbars",
                "--disable-background-timer-throttling",
                "--virtual-time-budget=10000",
                "--run-all-compositor-stages-before-draw",
                self.config["web_server_url"],
            ]

            logger.info(
                "Taking screenshot with Chrome (waiting for all resources to load)..."
            )
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)

            if result.returncode != 0:
                raise RuntimeError(f"Screenshot failed: {result.stderr}")

            if not os.path.exists(self.config["screenshot_path"]):
                raise RuntimeError("Screenshot file not created")

            logger.info(f"Screenshot saved to {self.config['screenshot_path']}")
            return True

        except Exception as e:
            logger.error(f"Mac screenshot failed: {e}")
            return False

    def _screenshot_linux(self):
        """Take screenshot on Linux/Pi using chromium-browser"""
        try:
            cmd = [
                "/usr/bin/chromium",
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--allow-running-insecure-content",
                f"--window-size={self.config['display_width']},{self.config['display_height']}",
                f"--screenshot={self.config['screenshot_path']}",
                "--force-device-scale-factor=1",  # Ensure 1:1 pixel rendering
                "--hide-scrollbars",  # Hide any scrollbars
                "--disable-background-timer-throttling",  # Ensure full rendering
                "--virtual-time-budget=10000",  # Wait 10 seconds for all resources
                "--run-all-compositor-stages-before-draw",
                self.config["web_server_url"],
            ]

            logger.info(
                "Taking screenshot with Chromium (waiting for all resources to load)..."
            )
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)

            if result.returncode != 0:
                raise RuntimeError(f"Screenshot failed: {result.stderr}")

            if not os.path.exists(self.config["screenshot_path"]):
                raise RuntimeError("Screenshot file not created")

            logger.info(f"Screenshot saved to {self.config['screenshot_path']}")
            return True

        except Exception as e:
            logger.error(f"Linux screenshot failed: {e}")
            return False

    def process_image(self):
        """Process screenshot for eink display"""
        try:
            img = Image.open(self.config["screenshot_path"])

            # Resize if needed
            target_size = (self.config["display_width"], self.config["display_height"])
            if img.size != target_size:
                img = img.resize(target_size, Image.LANCZOS)
                logger.info(f"Resized image to {target_size}")

            # Convert to RGB if needed
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Apply dithering if enabled (for both dev and Pi modes)
            if self.config.get("apply_dithering", False):
                img = self._apply_eink_dithering(img)
                logger.info("Applied e-ink dithering")

            return img
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            return None

    def _apply_eink_dithering(self, img):
        """Apply 7-color dithering to match e-ink display output"""
        try:
            # Try using Inky's own palette generation (if on Pi)
            if self.is_pi and self.inky:
                saturation = self.config.get("dither_saturation", 0.8)
                palette = self.inky._palette_blend(saturation, dtype="uint24")

                # Try hitherdither if available (better quality)
                try:
                    import hitherdither

                    # Create hitherdither palette from Inky palette
                    hither_palette = hitherdither.palette.Palette(palette)

                    # Apply Bayer dithering (Pimoroni's recommended method)
                    dithered = hitherdither.ordered.bayer.bayer_dithering(
                        img, hither_palette, thresholds=[64, 64, 64], order=8
                    )
                    logger.info(
                        f"Applied Bayer dithering with {len(palette)} colors from Inky palette"
                    )
                except ImportError:
                    # Fallback to Pillow quantization
                    dithered = img.quantize(
                        colors=6, dither=Image.Dither.FLOYDSTEINBERG
                    )
                    logger.info("Applied Floyd-Steinberg dithering (Pillow fallback)")
            else:
                # Dev mode: use exact Inky 6-color palette
                inky_palette = [
                    (0, 0, 0),  # Black
                    (255, 255, 255),  # White
                    (255, 0, 0),  # Red
                    (0, 255, 0),  # Green
                    (0, 0, 255),  # Blue
                    (255, 255, 0),  # Yellow
                ]

                # Create palette image for quantization
                palette_img = Image.new("P", (1, 1))
                palette_data = []
                for color in inky_palette:
                    palette_data.extend(color)
                palette_data.extend([0] * (768 - len(palette_data)))  # Pad to 768
                palette_img.putpalette(palette_data)

                dithered = img.quantize(
                    palette=palette_img, dither=Image.Dither.FLOYDSTEINBERG
                )
                logger.info("Applied Inky 6-color dithering (dev mode)")

            # Convert back to RGB for consistent handling
            return dithered.convert("RGB")

        except Exception as e:
            logger.warning(f"Dithering failed, using original image: {e}")
            return img

    def update_display(self, img):
        """Update the eink display or save for testing"""
        if self.is_pi and self.inky:
            try:
                # Convert image for eink display
                self.inky.set_image(img)
                self.inky.show()
                logger.info("Updated eink display")
                return True
            except Exception as e:
                logger.error(f"Display update failed: {e}")
                return False
        else:
            # Save for testing on Mac
            test_path = "test_display_output.png"
            img.save(test_path)
            logger.info(f"Test mode: saved display image to {test_path}")
            return True
