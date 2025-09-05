#!/usr/bin/env python3
"""
Direct eink display controller for E-Ink Scoreboard
Works on both Mac (for testing) and Raspberry Pi (with actual eink display)
"""

import os
import sys
import time
import json
import logging
import platform
import subprocess
from datetime import datetime
from pathlib import Path
from PIL import Image
import requests


# Load game status configuration
def load_game_status_config():
    """Load game status patterns from JSON config"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'game-status-config.json')
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Could not load game status config: {e}")
        raise

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default configuration (will be overridden by config file)
CONFIG = {
    "web_server_url": "http://localhost:5001/display",
    "screenshot_path": "/tmp/sports_display.png",
    "display_width": 800,
    "display_height": 480,
    "screenshot_scale": 1,
    "refresh_interval": 120,
    "apply_dithering": True,
    "dither_saturation": 0.8,
    "max_retries": 3,
    "retry_delay": 5
}

class EinkDisplayController:
    def __init__(self, config=None):
        self.config = config or CONFIG
        self.is_mac = platform.system() == "Darwin"
        self.is_pi = platform.system() == "Linux" and self._is_raspberry_pi()
        
        if self.is_pi:
            try:
                # Try auto-detection first
                from inky.auto import auto
                self.inky = auto()
                logger.info(f"Auto-detected Inky display: {self.inky.width}x{self.inky.height}")
            except ImportError as e:
                logger.error(f"Inky library not found: {e}. Install with: pip install inky")
                sys.exit(1)
            except Exception as e:
                # Fallback to Inky Impression 7.3" if auto-detection fails
                logger.warning(f"Auto-detection failed ({e}), trying Inky Impression 7.3...")
                try:
                    from inky import Inky_Impressions_7
                    self.inky = Inky_Impressions_7()
                    logger.info(f"Initialized Inky Impression 7.3: {self.inky.width}x{self.inky.height}")
                except Exception as e2:
                    logger.error(f"Failed to initialize Inky display: {e2}")
                    sys.exit(1)
        else:
            self.inky = None
            logger.info("Running in test mode (no physical eink display)")
    
    def _is_raspberry_pi(self):
        """Check if running on Raspberry Pi"""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                return 'Raspberry Pi' in cpuinfo or 'BCM' in cpuinfo
        except FileNotFoundError:
            return False
    
    def wait_for_server(self, timeout=60):
        """Wait for the web server to be available"""
        logger.info(f"Waiting for server at {self.config['web_server_url']}")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(self.config['web_server_url'], timeout=5)
                if response.status_code == 200:
                    logger.info("Server is ready")
                    return True
            except requests.RequestException:
                pass
            
            time.sleep(2)
        
        logger.error(f"Server not available after {timeout} seconds")
        return False
    
    def check_active_games(self):
        """Check if there are any active games by fetching game data"""
        try:
            # Load game status config
            status_config = load_game_status_config()
            
            # Extract the base URL and get game data via API
            base_url = self.config['web_server_url'].replace('/display', '')
            api_url = f"{base_url}/api/scores/MLB"
            
            response = requests.get(api_url, timeout=10)
            if response.status_code != 200:
                logger.warning(f"Could not fetch game data: {response.status_code}")
                return True  # Default to updating if we can't check
            
            games = response.json()
            if not games:
                logger.info("No games found")
                return False
            
            # Check for active games (not scheduled, not final)
            active_games = []
            scheduled_games = []
            final_games = []
            
            for game in games:
                status = game.get('status', '').lower()
                
                # Active game conditions (using config)
                if any(keyword in status for keyword in status_config['activeGameStatuses']):
                    active_games.append(game)
                # Scheduled game conditions (using config)
                elif any(keyword in status for keyword in status_config['scheduledGameStatuses']):
                    scheduled_games.append(game)
                # Final game conditions (using config)
                elif any(keyword in status for keyword in status_config['finalGameStatuses']):
                    final_games.append(game)
                else:
                    # Unknown status, treat as active to be safe
                    active_games.append(game)
            
            logger.info(f"Games status: {len(active_games)} active, {len(scheduled_games)} scheduled, {len(final_games)} final")
            
            # Return True if there are active games OR if there are new scheduled games for the day
            return len(active_games) > 0
            
        except Exception as e:
            logger.error(f"Error checking active games: {e}")
            return True  # Default to updating if there's an error
    
    def take_screenshot(self):
        """Take screenshot using available method"""
        # Try Playwright first (works on both Mac and Pi)
        try:
            return self._screenshot_playwright()
        except ImportError:
            logger.info("Playwright not available, falling back to system Chromium")
            if self.is_mac:
                return self._screenshot_mac_chromium()
            else:
                return self._screenshot_linux()
    
    def _screenshot_playwright(self):
        """Take screenshot using Playwright (works on both Mac and Pi)"""
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            
            # Get scale factor from config
            scale_factor = self.config.get('screenshot_scale', 1)
            
            page = browser.new_page(
                viewport={
                    "width": self.config['display_width'], 
                    "height": self.config['display_height']
                },
                device_scale_factor=scale_factor  # High DPI rendering
            )
            
            logger.info(f"Taking screenshot with Playwright ({scale_factor}x DPI rendering)...")
            page.goto(self.config['web_server_url'], wait_until="networkidle")
            
            # Wait for images to load
            page.wait_for_timeout(5000)
            
            page.screenshot(path=self.config['screenshot_path'], full_page=False)
            browser.close()
            
            logger.info(f"Screenshot saved to {self.config['screenshot_path']}")
            return True

    def _screenshot_mac_chromium(self):
        """Take screenshot on Mac using Chrome headless fallback"""
        try:
            
            # Fallback to Chrome headless
            chrome_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chromium.app/Contents/MacOS/Chromium",
                "google-chrome",
                "chromium-browser"
            ]
            
            chrome_cmd = None
            for path in chrome_paths:
                if os.path.exists(path) or subprocess.run(["which", path], capture_output=True).returncode == 0:
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
                self.config['web_server_url']
            ]
            
            logger.info("Taking screenshot with Chrome (waiting for all resources to load)...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
            
            if result.returncode != 0:
                raise RuntimeError(f"Screenshot failed: {result.stderr}")
            
            if not os.path.exists(self.config['screenshot_path']):
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
                self.config['web_server_url']
            ]
            
            logger.info("Taking screenshot with Chromium (waiting for all resources to load)...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
            
            if result.returncode != 0:
                raise RuntimeError(f"Screenshot failed: {result.stderr}")
            
            if not os.path.exists(self.config['screenshot_path']):
                raise RuntimeError("Screenshot file not created")
                
            logger.info(f"Screenshot saved to {self.config['screenshot_path']}")
            return True
            
        except Exception as e:
            logger.error(f"Linux screenshot failed: {e}")
            return False
    
    def process_image(self):
        """Process screenshot for eink display"""
        try:
            img = Image.open(self.config['screenshot_path'])
            
            # Resize if needed
            target_size = (self.config['display_width'], self.config['display_height'])
            if img.size != target_size:
                img = img.resize(target_size, Image.LANCZOS)
                logger.info(f"Resized image to {target_size}")
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Apply dithering if enabled (for both dev and Pi modes)
            if self.config.get('apply_dithering', False):
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
                saturation = self.config.get('dither_saturation', 0.8)
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
                    logger.info(f"Applied Bayer dithering with {len(palette)} colors from Inky palette")
                except ImportError:
                    # Fallback to Pillow quantization
                    dithered = img.quantize(colors=6, dither=Image.Dither.FLOYDSTEINBERG)
                    logger.info("Applied Floyd-Steinberg dithering (Pillow fallback)")
            else:
                # Dev mode: use exact Inky 6-color palette
                inky_palette = [
                    (0, 0, 0),         # Black
                    (255, 255, 255),   # White
                    (255, 0, 0),       # Red  
                    (0, 255, 0),       # Green
                    (0, 0, 255),       # Blue
                    (255, 255, 0),     # Yellow
                ]
                
                # Create palette image for quantization
                palette_img = Image.new('P', (1, 1))
                palette_data = []
                for color in inky_palette:
                    palette_data.extend(color)
                palette_data.extend([0] * (768 - len(palette_data)))  # Pad to 768
                palette_img.putpalette(palette_data)
                
                dithered = img.quantize(palette=palette_img, dither=Image.Dither.FLOYDSTEINBERG)
                logger.info("Applied Inky 6-color dithering (dev mode)")
            
            # Convert back to RGB for consistent handling
            return dithered.convert('RGB')
            
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
    
    def refresh_display(self, force_update=False):
        """Complete refresh cycle: screenshot -> process -> display
        
        Display Update Logic:
        - force_update=True: Always updates display (used for new game days)
        - force_update=False: Only updates if there are active games running
        
        This prevents unnecessary e-ink refreshes when games are only scheduled
        but preserves the ability to update the display when games start.
        """
        logger.info("Starting display refresh...")
        
        # Check for active games unless forced
        if not force_update:
            has_active_games = self.check_active_games()
            if not has_active_games:
                logger.info("No active games found - skipping display update")
                return True  # Return success but skip display update
        
        # Take screenshot with retries
        screenshot_success = False
        for attempt in range(self.config['max_retries']):
            if self.take_screenshot():
                screenshot_success = True
                break
            else:
                if attempt < self.config['max_retries'] - 1:
                    logger.warning(f"Screenshot attempt {attempt + 1} failed, retrying...")
                    time.sleep(self.config['retry_delay'])
        
        if not screenshot_success:
            logger.error("Failed to take screenshot after all retries")
            return False
        
        # Process image
        img = self.process_image()
        if not img:
            return False
        
        # Update display
        return self.update_display(img)
    
    def run_continuous(self):
        """Run continuous refresh loop with smart game detection"""
        logger.info(f"Starting continuous refresh every {self.config['refresh_interval']} seconds")
        
        if not self.wait_for_server():
            return False
        
        last_game_date = None
        new_games_detected = False
        
        while True:
            try:
                # Check current game date
                current_date = datetime.now().strftime('%Y-%m-%d')
                
                # Force update if it's a new day or if new games were detected
                force_update = False
                if last_game_date != current_date:
                    logger.info(f"New game day detected: {current_date}")
                    last_game_date = current_date
                    new_games_detected = False
                    force_update = True
                
                # Check for scheduled games that might have started
                if not force_update:
                    try:
                        base_url = self.config['web_server_url'].replace('/display', '')
                        api_url = f"{base_url}/api/scores/MLB"
                        response = requests.get(api_url, timeout=10)
                        
                        if response.status_code == 200:
                            games = response.json()
                            scheduled_games = [g for g in games if any(kw in g.get('status', '').lower() for kw in ['pm et', 'am et', 'scheduled'])]
                            
                            # If we have scheduled games and haven't detected new games yet, check if we should update once
                            if scheduled_games and not new_games_detected:
                                logger.info(f"Found {len(scheduled_games)} scheduled games - updating display once for new day")
                                new_games_detected = True
                                force_update = True
                    except Exception as e:
                        logger.warning(f"Error checking for new games: {e}")
                
                success = self.refresh_display(force_update=force_update)
                
                if success and not force_update:
                    logger.info(f"Checked for active games at {datetime.now()}")
                elif success and force_update:
                    logger.info(f"Display updated at {datetime.now()}")
                else:
                    logger.error("Display refresh failed")
                
                logger.info(f"Next check in {self.config['refresh_interval']} seconds")
                time.sleep(int(self.config['refresh_interval']))
                
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                time.sleep(self.config['retry_delay'])


def load_config(config_file="eink_config.json"):
    """Load configuration from file if it exists"""
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
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
    parser.add_argument("--once", action="store_true", help="Update display once and exit")
    parser.add_argument("--config", default="eink_config.json", help="Configuration file path")
    parser.add_argument("--interval", type=int, help="Refresh interval in seconds")
    parser.add_argument("--url", help="Web server URL")
    parser.add_argument("--dithering", action="store_true", help="Apply e-ink dithering for testing")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override with command line arguments
    if args.interval:
        config['refresh_interval'] = args.interval
    if args.url:
        config['web_server_url'] = args.url
    if args.dithering:
        config['apply_dithering'] = True
        logger.info("Dithering enabled via command line flag")
    
    # Create controller
    controller = EinkDisplayController(config)
    
    if args.once:
        # Single update (always force when using --once)
        if not controller.wait_for_server():
            sys.exit(1)
        
        success = controller.refresh_display(force_update=True)
        sys.exit(0 if success else 1)
    else:
        # Continuous mode
        controller.run_continuous()


if __name__ == "__main__":
    main()