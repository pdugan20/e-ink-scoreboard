#!/usr/bin/env python3
"""
Direct eink display controller for sports scores
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

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
CONFIG = {
    "web_server_url": "http://localhost:5001/display",
    "screenshot_path": "/tmp/sports_display.png",
    "display_width": 800,
    "display_height": 480,
    "screenshot_scale": 2,  # Take screenshot at 2x resolution for clarity
    "refresh_interval": 120,  # 2 minutes
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
    
    def take_screenshot(self):
        """Take screenshot using available method"""
        if self.is_mac:
            return self._screenshot_mac()
        else:
            return self._screenshot_linux()
    
    def _screenshot_mac(self):
        """Take screenshot on Mac using Playwright for precise viewport control"""
        try:
            # Try Playwright first for better viewport control
            try:
                from playwright.sync_api import sync_playwright
                
                with sync_playwright() as p:
                    browser = p.chromium.launch()
                    
                    # Get scale factor from config
                    scale_factor = self.config.get('screenshot_scale', 2)
                    
                    page = browser.new_page(
                        viewport={
                            "width": self.config['display_width'], 
                            "height": self.config['display_height']
                        },
                        device_scale_factor=scale_factor  # High DPI rendering
                    )
                    
                    logger.info(f"Taking screenshot with Playwright (2x DPI for crisp rendering)...")
                    page.goto(self.config['web_server_url'], wait_until="networkidle")
                    
                    # Wait for images to load
                    page.wait_for_timeout(5000)
                    
                    page.screenshot(path=self.config['screenshot_path'], full_page=False)
                    browser.close()
                    
                    logger.info(f"Screenshot saved to {self.config['screenshot_path']}")
                    return True
                    
            except ImportError:
                logger.info("Playwright not available, falling back to Chrome...")
                pass
            
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
                "chromium",
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
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
            
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
            
            return img
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            return None
    
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
    
    def refresh_display(self):
        """Complete refresh cycle: screenshot -> process -> display"""
        logger.info("Starting display refresh...")
        
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
        """Run continuous refresh loop"""
        logger.info(f"Starting continuous refresh every {self.config['refresh_interval']} seconds")
        
        if not self.wait_for_server():
            return False
        
        while True:
            try:
                success = self.refresh_display()
                if success:
                    logger.info(f"Display updated successfully at {datetime.now()}")
                else:
                    logger.error("Display update failed")
                
                logger.info(f"Next refresh in {self.config['refresh_interval']} seconds")
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
    
    parser = argparse.ArgumentParser(description="Sports Scores Eink Display Controller")
    parser.add_argument("--once", action="store_true", help="Update display once and exit")
    parser.add_argument("--config", default="eink_config.json", help="Configuration file path")
    parser.add_argument("--interval", type=int, help="Refresh interval in seconds")
    parser.add_argument("--url", help="Web server URL")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override with command line arguments
    if args.interval:
        config['refresh_interval'] = args.interval
    if args.url:
        config['web_server_url'] = args.url
    
    # Create controller
    controller = EinkDisplayController(config)
    
    if args.once:
        # Single update
        if not controller.wait_for_server():
            sys.exit(1)
        
        success = controller.refresh_display()
        sys.exit(0 if success else 1)
    else:
        # Continuous mode
        controller.run_continuous()


if __name__ == "__main__":
    main()