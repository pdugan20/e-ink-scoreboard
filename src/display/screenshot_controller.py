"""
Screenshot and image processing logic for e-ink display.
"""

import logging
import platform
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
        if not self.is_pi:
            logger.info("Not on Raspberry Pi, skipping Inky display initialization")
            return None

        try:
            # Try auto-detection first
            from inky.auto import auto  # type: ignore

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
                from inky import Inky_Impressions_7  # type: ignore

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

    def _check_memory_available(self):
        """Check if there's enough memory to safely take a screenshot."""
        try:
            mem = psutil.virtual_memory()
            available_mb = mem.available / 1024 / 1024

            # Based on logs, problems occur when available memory < 200MB
            # But we can try with 150MB for important updates
            MIN_MEMORY_MB = 200
            CRITICAL_MIN_MB = 150

            if available_mb < MIN_MEMORY_MB:
                logger.warning(
                    f"Low memory: {available_mb:.0f}MB available (minimum {MIN_MEMORY_MB}MB recommended)"
                )

                # Try to free memory
                import gc

                gc.collect()

                # Kill any hanging browsers to free memory
                self._kill_hanging_browsers()

                # Check again after cleanup
                mem = psutil.virtual_memory()
                available_mb = mem.available / 1024 / 1024

                if available_mb < CRITICAL_MIN_MB:
                    logger.error(
                        f"Critically low memory after cleanup: {available_mb:.0f}MB (minimum {CRITICAL_MIN_MB}MB)"
                    )
                    return False
                elif available_mb < MIN_MEMORY_MB:
                    logger.warning(
                        f"Memory still below recommended after cleanup: {available_mb:.0f}MB, proceeding cautiously"
                    )

            logger.debug(f"Memory check passed: {available_mb:.0f}MB available")
            return True

        except Exception as e:
            logger.warning(f"Could not check memory: {e}")
            return True  # Proceed anyway if we can't check

    def take_screenshot(self):
        """Take screenshot using Playwright with browser process management."""
        # Check memory before attempting screenshot
        if not self._check_memory_available():
            logger.warning("Insufficient memory for screenshot, skipping this cycle")
            return False

        with self._browser_process_manager():
            try:
                # Add a hard timeout for the entire screenshot operation
                import signal

                def timeout_handler(signum, frame):
                    raise TimeoutError(
                        "Screenshot operation timed out after 120 seconds"
                    )

                # Set alarm for 2 minutes (should be plenty based on logs showing 20-40s normal)
                if not self.is_mac:  # signal.alarm doesn't work well on Mac
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(120)

                try:
                    success = self._screenshot_playwright()
                    log_after_screenshot(logger, success)

                    # Force garbage collection after screenshot to free memory
                    import gc

                    gc.collect()

                    return success
                finally:
                    if not self.is_mac:
                        signal.alarm(0)  # Cancel the alarm

            except TimeoutError as e:
                logger.error(f"Screenshot timed out: {e}")
                logger.info("Killing any hanging browser processes...")
                self._kill_hanging_browsers()
                log_after_screenshot(logger, False)
                return False
            except ImportError as e:
                logger.error(f"Playwright not available: {e}")
                logger.error(
                    "Please install Playwright: pip install playwright && playwright install chromium"
                )
                log_after_screenshot(logger, False)
                return False
            except Exception as e:
                logger.error(f"Screenshot failed: {e}")
                log_after_screenshot(logger, False)
                return False

    def _screenshot_playwright(self):
        """Take screenshot using Playwright with Chromium (works on both Mac and Pi)"""
        from playwright.sync_api import sync_playwright

        browser = None
        try:
            with sync_playwright() as p:
                # Memory-optimized args for Raspberry Pi
                browser_args = [
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-software-rasterizer",
                    "--disable-background-timer-throttling",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-renderer-backgrounding",
                    "--disable-features=TranslateUI",
                    "--disable-ipc-flooding-protection",
                    "--max_old_space_size=256",  # Limit memory usage
                    "--single-process",  # Use single process to reduce memory
                ]

                browser = p.chromium.launch(headless=True, args=browser_args)

                # Get scale factor from config
                scale_factor = self.config.get("screenshot_scale", 1)

                page = browser.new_page(
                    viewport={
                        "width": self.config["display_width"],
                        "height": self.config["display_height"],
                    },
                    device_scale_factor=scale_factor,  # High DPI rendering
                    color_scheme="light",  # Force light mode for consistent rendering
                )

                logger.info(
                    f"Taking screenshot with Playwright ({scale_factor}x DPI rendering)..."
                )

                # Increase timeout for slower Pi and RSS feed loading
                page.set_default_timeout(60000)  # 60 seconds (reduced from 90)

                try:
                    page.goto(
                        self.config["web_server_url"],
                        wait_until="networkidle",
                        timeout=60000,  # 60 seconds should be enough based on logs
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
