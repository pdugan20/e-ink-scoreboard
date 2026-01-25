"""
Screenshot and image processing logic for e-ink display.
"""

import logging
import platform
import time
from contextlib import contextmanager

import psutil
from PIL import Image

from config.memory_config import (
    BROWSER_JS_HEAP_MB,
    MEMORY_MINIMUM_MB,
    MEMORY_RECOMMENDED_MB,
)
from display.browser_cleanup import BrowserCleanup
from utils.logging_config import (
    log_after_screenshot,
    log_before_screenshot,
    log_browser_cleanup,
)

logger = logging.getLogger(__name__)


class ScreenshotController:
    """Handles taking screenshots and processing images for e-ink display."""

    def __init__(self, config, test_mode=False):
        self.config = config
        self.test_mode = test_mode  # Skip resource checks in test mode
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

            if available_mb < MEMORY_RECOMMENDED_MB:
                logger.warning(
                    f"Low memory: {available_mb:.0f}MB available (minimum {MEMORY_RECOMMENDED_MB}MB recommended)"
                )

                # Try to free memory
                import gc

                gc.collect()

                # Kill any hanging browsers to free memory
                self._kill_hanging_browsers()

                # Check again after cleanup
                mem = psutil.virtual_memory()
                available_mb = mem.available / 1024 / 1024

                if available_mb < MEMORY_MINIMUM_MB:
                    logger.error(
                        f"Critically low memory after cleanup: {available_mb:.0f}MB (minimum {MEMORY_MINIMUM_MB}MB)"
                    )
                    # Try emergency recovery
                    logger.info("Attempting emergency memory recovery...")
                    recovered_mb = BrowserCleanup.emergency_memory_recovery()
                    if recovered_mb < MEMORY_MINIMUM_MB:
                        logger.error(
                            f"Still low memory after emergency recovery: {recovered_mb:.0f}MB"
                        )
                        return False
                    logger.info(
                        f"Memory recovered to {recovered_mb:.0f}MB, proceeding..."
                    )
                elif available_mb < MEMORY_RECOMMENDED_MB:
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
                # Subprocess guardian now handles timeouts and resource checks
                success = self._screenshot_playwright()
                log_after_screenshot(logger, success)

                # Force garbage collection after screenshot to free memory
                import gc

                gc.collect()

                return success

            except TimeoutError as e:
                logger.error(f"Screenshot timed out: {e}")
                logger.info("Force killing ALL browser processes...")
                BrowserCleanup.force_kill_all_browsers()
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
        """Take screenshot using subprocess to prevent kernel hangs."""
        logger.debug("Starting screenshot subprocess...")

        # ONLY use subprocess - no fallback to prevent freezes
        return self._screenshot_subprocess()

    def _screenshot_subprocess(self):
        """Run screenshot in subprocess that can be killed if it hangs."""
        try:
            import json
            import os

            from .subprocess_guardian import run_safe_subprocess

            # Prepare config for subprocess
            config_data = {
                "web_server_url": self.config["web_server_url"],
                "screenshot_path": self.config["screenshot_path"],
                "display_width": self.config["display_width"],
                "display_height": self.config["display_height"],
                "screenshot_scale": self.config.get("screenshot_scale", 1),
                "browser_js_heap_mb": BROWSER_JS_HEAP_MB,
            }
            config_json = json.dumps(config_data)

            # Path to worker script
            worker_path = os.path.join(
                os.path.dirname(__file__), "screenshot_worker.py"
            )

            # Run subprocess with guardian protection
            logger.info("Taking screenshot via guarded subprocess...")
            # Skip resource checks in test mode (--once or --force)
            success, stdout, stderr = run_safe_subprocess(
                ["python", worker_path, config_json],
                timeout=150,  # Increased for slow Pi Zero
                check_resources=not self.test_mode,  # Skip checks in test mode
                critical_operation=True,  # Screenshots are critical
            )

            if success:
                logger.info("Subprocess screenshot succeeded")
                return True
            else:
                logger.error(f"Subprocess failed: {stderr}")
                # Guardian already handles cleanup, but ensure browsers are dead
                BrowserCleanup.force_kill_all_browsers()
                return False

        except Exception as e:
            logger.error(f"Subprocess screenshot error: {e}")
            # Emergency cleanup
            BrowserCleanup.force_kill_all_browsers()
            return False

    def _screenshot_direct_original(self):
        """Original implementation - DO NOT USE."""
        from playwright.sync_api import sync_playwright

        browser = None
        try:
            logger.debug("Creating Playwright instance...")
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
                    f"--js-flags=--max-old-space-size={BROWSER_JS_HEAP_MB}",  # Limit JS heap
                    "--disable-background-timer-throttling",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-renderer-backgrounding",
                    "--single-process",  # Critical for Pi Zero memory constraints
                    "--disable-features=site-per-process",
                    "--memory-pressure-off",
                    "--max_old_space_size=96",  # Additional JS heap limit
                    "--aggressive-cache-discard",  # Discard cache aggressively
                    "--disable-features=RendererCodeIntegrity",  # Reduce overhead
                ]

                logger.debug(
                    f"Launching browser with {len(browser_args)} optimization flags..."
                )
                browser = p.chromium.launch(headless=True, args=browser_args)
                logger.debug("Browser launched successfully")

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

                # Reduce timeout for low-memory conditions
                page.set_default_timeout(20000)  # 20 seconds

                try:
                    # Load the page and wait for network to settle
                    page.goto(
                        self.config["web_server_url"],
                        wait_until="domcontentloaded",  # Don't wait for all resources
                        timeout=30000,  # 30 seconds
                    )

                    # Wait for games to be rendered by JavaScript
                    # Either wait for game cards OR error message
                    try:
                        page.wait_for_selector(
                            ".game-card, .game-pill, #games > div",
                            timeout=15000,  # 15 seconds for content
                        )
                        logger.info("Game content detected")
                    except Exception:
                        # If no games appear, wait a bit more for JS to execute
                        logger.warning("No game content found, waiting for JS...")
                        page.wait_for_timeout(8000)

                except Exception as e:
                    # Last resort - just wait for JS to execute
                    logger.warning(f"Page load issue: {e}")
                    page.wait_for_timeout(10000)  # Give JS 10 seconds

                page.screenshot(path=self.config["screenshot_path"], full_page=False)

                # Ensure page and browser are properly closed
                page.close()
                browser.close()
                browser = None

                # Extra cleanup for Playwright node processes
                time.sleep(1)  # Give browser time to cleanup
                BrowserCleanup.force_kill_all_browsers()

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
                logger.info("Starting e-ink display update...")

                # Add a simple timeout using signal alarm
                import signal

                def timeout_handler(signum, frame):
                    raise TimeoutError(
                        "E-ink display update timed out after 90 seconds"
                    )

                # Set alarm for 90 seconds (usually takes ~28 seconds)
                if not self.is_mac:
                    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(90)

                try:
                    self.inky.show()
                    logger.info("Updated eink display")
                    return True
                finally:
                    # Cancel alarm
                    if not self.is_mac:
                        signal.alarm(0)
                        signal.signal(signal.SIGALRM, old_handler)
            except Exception as e:
                logger.error(f"Display update failed: {e}")
                return False
        else:
            # Save for testing on Mac
            test_path = "test_display_output.png"
            img.save(test_path)
            logger.info(f"Test mode: saved display image to {test_path}")
            return True
