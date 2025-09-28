#!/usr/bin/env python3
"""
Enhanced Watchdog Monitor - Prevents system freezes with multiple detection methods.

This aggressive watchdog monitors:
1. Screenshot file age
2. Process state (D/zombie/high CPU)
3. Memory usage patterns
4. Heartbeat file updates
5. System load averages
"""

import logging
import os
import signal
import subprocess
import time
from datetime import datetime, timedelta

import psutil

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration - use environment variables or defaults
SCREENSHOT_PATH = os.environ.get("EINK_SCREENSHOT_PATH", "/tmp/sports_display.png")
HEARTBEAT_PATH = os.environ.get("EINK_HEARTBEAT_PATH", "/tmp/eink_heartbeat")
LOG_PATH = os.environ.get(
    "EINK_LOG_PATH", os.path.expanduser("~/logs/eink_display.log")
)
MAX_SCREENSHOT_AGE_MINUTES = int(os.environ.get("EINK_MAX_SCREENSHOT_AGE", "8"))
MAX_HEARTBEAT_AGE_SECONDS = int(os.environ.get("EINK_MAX_HEARTBEAT_AGE", "120"))
CHECK_INTERVAL = int(os.environ.get("EINK_CHECK_INTERVAL", "30"))
SERVICE_NAME = os.environ.get("EINK_SERVICE_NAME", "sports-display.service")

# Thresholds
MAX_MEMORY_MB = 100  # Restart if process uses more than this
MAX_LOAD_AVG = 4.0  # Restart if load average exceeds this
MIN_FREE_MEMORY_MB = 150  # Restart if system memory drops below this
MAX_CONSECUTIVE_FAILURES = 3  # Restart after this many check failures


class EnhancedWatchdog:
    def __init__(self):
        self.last_restart = datetime.now() - timedelta(hours=1)
        self.consecutive_failures = 0
        self.last_screenshot_time = None
        self.frozen_indicators = set()

    def check_heartbeat(self) -> bool:
        """Check if heartbeat file is being updated."""
        try:
            if not os.path.exists(HEARTBEAT_PATH):
                logger.warning("No heartbeat file found")
                return False

            age = time.time() - os.path.getmtime(HEARTBEAT_PATH)
            if age > MAX_HEARTBEAT_AGE_SECONDS:
                logger.warning(f"Heartbeat stale: {age:.0f}s old")
                return False

            return True
        except Exception as e:
            logger.error(f"Heartbeat check failed: {e}")
            return False

    def check_screenshot_age(self) -> bool:
        """Check if screenshot is being updated."""
        try:
            if not os.path.exists(SCREENSHOT_PATH):
                logger.warning("No screenshot file found")
                return False

            age_minutes = (time.time() - os.path.getmtime(SCREENSHOT_PATH)) / 60

            # Track if screenshot is stuck
            current_mtime = os.path.getmtime(SCREENSHOT_PATH)
            if self.last_screenshot_time == current_mtime:
                self.consecutive_failures += 1
                logger.warning(
                    f"Screenshot unchanged for {self.consecutive_failures} checks"
                )
            else:
                self.last_screenshot_time = current_mtime
                self.consecutive_failures = 0

            if age_minutes > MAX_SCREENSHOT_AGE_MINUTES:
                logger.warning(f"Screenshot too old: {age_minutes:.1f} minutes")
                return False

            return True
        except Exception as e:
            logger.error(f"Screenshot check failed: {e}")
            return False

    def check_process_health(self) -> bool:
        """Check if main process is healthy."""
        try:
            # Find the main process
            for proc in psutil.process_iter(["pid", "name", "cmdline", "status"]):
                if "eink_display.py" in " ".join(proc.info.get("cmdline", [])):
                    # Check for zombie/dead state
                    if proc.info["status"] == psutil.STATUS_ZOMBIE:
                        logger.error("Main process is a zombie")
                        return False

                    # Check for D (uninterruptible) state
                    if proc.info["status"] == "disk-sleep":
                        logger.error("Main process in D state (uninterruptible)")
                        return False

                    # Check memory usage
                    memory_mb = proc.memory_info().rss / (1024 * 1024)
                    if memory_mb > MAX_MEMORY_MB:
                        logger.warning(
                            f"Process using too much memory: {memory_mb:.1f}MB"
                        )
                        self.frozen_indicators.add("high_memory")
                        if len(self.frozen_indicators) > 1:
                            return False

                    # Check CPU usage (stuck in busy loop?)
                    cpu_percent = proc.cpu_percent(interval=1)
                    if cpu_percent > 90:
                        logger.warning(f"Process using high CPU: {cpu_percent:.1f}%")
                        self.frozen_indicators.add("high_cpu")
                        if len(self.frozen_indicators) > 1:
                            return False

                    return True

            logger.warning("Main process not found")
            return False

        except Exception as e:
            logger.error(f"Process health check failed: {e}")
            return True  # Assume OK if can't check

    def check_system_resources(self) -> bool:
        """Check overall system health."""
        try:
            # Check system memory
            memory = psutil.virtual_memory()
            available_mb = memory.available / (1024 * 1024)
            if available_mb < MIN_FREE_MEMORY_MB:
                logger.warning(f"Low system memory: {available_mb:.0f}MB available")
                self.frozen_indicators.add("low_memory")
                if len(self.frozen_indicators) > 1:
                    return False

            # Check load average
            load_avg = os.getloadavg()[0]
            if load_avg > MAX_LOAD_AVG:
                logger.warning(f"High system load: {load_avg:.2f}")
                self.frozen_indicators.add("high_load")
                if len(self.frozen_indicators) > 1:
                    return False

            # Check for stuck browser processes
            browser_count = 0
            for proc in psutil.process_iter(["name"]):
                if (
                    "chromium" in proc.info["name"].lower()
                    or "chrome" in proc.info["name"].lower()
                ):
                    browser_count += 1

            if browser_count > 3:
                logger.warning(f"Too many browser processes: {browser_count}")
                self.frozen_indicators.add("browser_leak")
                if len(self.frozen_indicators) > 2:
                    return False

            return True

        except Exception as e:
            logger.error(f"System resource check failed: {e}")
            return True

    def check_log_activity(self) -> bool:
        """Check if logs are still being written."""
        try:
            if not os.path.exists(LOG_PATH):
                return True  # Log might not exist yet

            # Check last modification time
            age_seconds = time.time() - os.path.getmtime(LOG_PATH)
            if age_seconds > 300:  # No logs in 5 minutes
                logger.warning(f"No log activity for {age_seconds:.0f} seconds")
                return False

            return True

        except Exception as e:
            logger.error(f"Log check failed: {e}")
            return True

    def force_restart(self, reason: str):
        """Force restart the service with aggressive cleanup."""
        logger.error(f"FORCE RESTART: {reason}")

        try:
            # Step 1: Try graceful stop
            logger.info("Attempting graceful stop...")
            subprocess.run(
                ["sudo", "systemctl", "stop", SERVICE_NAME], timeout=10, check=False
            )
            time.sleep(2)

        except subprocess.TimeoutExpired:
            logger.warning("Graceful stop timed out")

        try:
            # Step 2: Kill all related processes
            logger.info("Killing all related processes...")
            kill_commands = [
                ["sudo", "pkill", "-9", "-f", "eink_display.py"],
                ["sudo", "pkill", "-9", "-f", "screenshot_worker.py"],
                ["sudo", "pkill", "-9", "-f", "playwright"],
                ["sudo", "pkill", "-9", "-f", "chromium"],
                ["sudo", "pkill", "-9", "-f", "chrome"],
            ]

            for cmd in kill_commands:
                subprocess.run(cmd, timeout=5, check=False)

            time.sleep(2)

            # Step 3: Clean up temp files
            logger.info("Cleaning temp files...")
            temp_files = [SCREENSHOT_PATH, HEARTBEAT_PATH, "/tmp/.X99-lock"]
            for f in temp_files:
                try:
                    if os.path.exists(f):
                        os.remove(f)
                except (OSError, PermissionError):
                    pass

            # Step 4: Clear system caches (helps with memory)
            logger.info("Clearing system caches...")
            subprocess.run(["sudo", "sync"], timeout=5, check=False)
            subprocess.run(
                ["sudo", "sh", "-c", "echo 3 > /proc/sys/vm/drop_caches"],
                timeout=5,
                check=False,
            )

            # Step 5: Start service
            logger.info("Starting service...")
            subprocess.run(
                ["sudo", "systemctl", "start", SERVICE_NAME], timeout=30, check=True
            )

            logger.info("Service restarted successfully")
            self.last_restart = datetime.now()
            self.consecutive_failures = 0
            self.frozen_indicators.clear()

            # Wait for service to stabilize
            time.sleep(30)

        except Exception as e:
            logger.error(f"Force restart failed: {e}")
            # Last resort - reboot system
            logger.critical("Unable to restart service, considering system reboot...")
            # Uncomment to enable auto-reboot:
            # subprocess.run(["sudo", "reboot"], check=False)

    def run_checks(self) -> bool:
        """Run all health checks."""
        checks = {
            "heartbeat": self.check_heartbeat(),
            "screenshot": self.check_screenshot_age(),
            "process": self.check_process_health(),
            "resources": self.check_system_resources(),
            "logs": self.check_log_activity(),
        }

        failed_checks = [name for name, passed in checks.items() if not passed]

        if failed_checks:
            logger.warning(f"Failed checks: {failed_checks}")

            # Multiple failures or critical single failure
            if len(failed_checks) >= 2 or "process" in failed_checks:
                return False

            # Consecutive screenshot failures
            if self.consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                logger.error(
                    f"Too many consecutive failures: {self.consecutive_failures}"
                )
                return False

        else:
            # All checks passed
            if self.frozen_indicators:
                logger.info(f"Clearing warning indicators: {self.frozen_indicators}")
                self.frozen_indicators.clear()

        return True

    def should_restart(self) -> bool:
        """Determine if we should restart based on cooldown."""
        time_since_restart = datetime.now() - self.last_restart
        cooldown_seconds = 180  # 3 minute minimum between restarts

        if time_since_restart.total_seconds() < cooldown_seconds:
            remaining = cooldown_seconds - time_since_restart.total_seconds()
            logger.info(f"Restart cooldown: {remaining:.0f}s remaining")
            return False

        return True

    def run(self):
        """Main watchdog loop."""
        logger.info("=" * 60)
        logger.info(f"Enhanced Watchdog Started for {SERVICE_NAME}")
        logger.info(
            f"Screenshot: {SCREENSHOT_PATH} (max {MAX_SCREENSHOT_AGE_MINUTES} min)"
        )
        logger.info(
            f"Heartbeat: {HEARTBEAT_PATH} (max {MAX_HEARTBEAT_AGE_SECONDS} sec)"
        )
        logger.info(f"Check interval: {CHECK_INTERVAL} seconds")
        logger.info("=" * 60)

        while True:
            try:
                if not self.run_checks():
                    if self.should_restart():
                        self.force_restart("Multiple health check failures")
                    else:
                        logger.warning("Would restart but in cooldown period")

                time.sleep(CHECK_INTERVAL)

            except KeyboardInterrupt:
                logger.info("Watchdog stopped by user")
                break
            except Exception as e:
                logger.error(f"Watchdog error: {e}")
                time.sleep(CHECK_INTERVAL)


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, shutting down...")
    exit(0)


if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Run watchdog
    watchdog = EnhancedWatchdog()
    watchdog.run()
