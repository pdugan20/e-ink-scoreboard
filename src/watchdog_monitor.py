#!/usr/bin/env python3
"""
Watchdog Monitor - Prevents system freezes with multiple detection methods.

Runs as a separate process (sports-watchdog.service) to detect and recover
from hangs in the main display service.

Monitors:
1. Screenshot file age (is the display updating?)
2. Process state (zombie, D-state, high CPU/memory) and system resources
3. Browser process leaks
4. Heartbeat file updates
5. Log activity

Thresholds scale with the configured refresh_interval from eink_config.json.
A startup grace period avoids false positives while the display service
takes its first screenshot.

Escalates to full system reboot after repeated restart failures.
"""

import json
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
CHECK_INTERVAL = int(os.environ.get("EINK_CHECK_INTERVAL", "30"))
SERVICE_NAME = os.environ.get("EINK_SERVICE_NAME", "sports-display.service")
CONFIG_PATH = os.environ.get("EINK_CONFIG_PATH", "src/eink_config.json")

# Thresholds
MAX_MEMORY_MB = 100  # Restart if process uses more than this
MAX_LOAD_AVG = 4.0  # Restart if load average exceeds this
MIN_FREE_MEMORY_MB = 150  # Restart if system memory drops below this
MAX_CONSECUTIVE_FAILURES = 3  # Restart after this many check failures


def load_refresh_interval():
    """Read refresh_interval from eink_config.json."""
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH) as f:
                config = json.load(f)
            interval = int(config.get("refresh_interval", 360))
            logger.info(f"Loaded refresh_interval from config: {interval}s")
            return interval
    except Exception as e:
        logger.warning(f"Could not read config, using default: {e}")
    return 360


def compute_thresholds(refresh_interval):
    """Derive watchdog thresholds from the configured refresh interval.

    Returns a dict with:
        max_screenshot_age_minutes: how old a screenshot can be before it's stale
        max_heartbeat_age_seconds: how old the heartbeat file can be
        log_inactivity_seconds: how long without log writes before flagging
        startup_grace_seconds: how long to skip checks after watchdog start
    """
    refresh_minutes = refresh_interval / 60

    return {
        # Screenshot can be up to 2x the refresh interval + 5 min buffer,
        # minimum 10 minutes (covers the default 6-min interval)
        "max_screenshot_age_minutes": max(10, refresh_minutes * 2 + 5),
        # Heartbeat thread writes every 30s, so 120s gives 4x headroom
        "max_heartbeat_age_seconds": 120,
        # Log inactivity: refresh interval + 5 min buffer, minimum 10 min
        "log_inactivity_seconds": max(600, refresh_interval + 300),
        # Grace period: enough time for server wait (60s) + memory wait (300s)
        # + first screenshot (90s), scaled up for longer intervals
        "startup_grace_seconds": max(300, refresh_interval + 120),
    }


class WatchdogMonitor:
    def __init__(self):
        self.last_restart = datetime.now() - timedelta(hours=1)
        self.consecutive_failures = 0
        self.last_screenshot_time = None
        self.frozen_indicators = set()
        self.startup_time = time.time()

        # Load config-aware thresholds
        self.refresh_interval = load_refresh_interval()
        self.thresholds = compute_thresholds(self.refresh_interval)

        # Reboot escalation tracking
        self.restart_timestamps = []
        self.max_restarts_before_reboot = 3
        self.reboot_window_seconds = 3600  # 1 hour

    def _in_grace_period(self) -> bool:
        """Check if we're still in the startup grace period."""
        elapsed = time.time() - self.startup_time
        grace = self.thresholds["startup_grace_seconds"]
        if elapsed < grace:
            remaining = grace - elapsed
            logger.debug(f"Startup grace period: {remaining:.0f}s remaining")
            return True
        return False

    def check_heartbeat(self) -> bool:
        """Check if heartbeat file is being updated."""
        try:
            if not os.path.exists(HEARTBEAT_PATH):
                logger.warning("No heartbeat file found")
                return False

            age = time.time() - os.path.getmtime(HEARTBEAT_PATH)
            max_age = self.thresholds["max_heartbeat_age_seconds"]
            if age > max_age:
                logger.warning(f"Heartbeat stale: {age:.0f}s old (max {max_age}s)")
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
            max_age = self.thresholds["max_screenshot_age_minutes"]

            # Track if screenshot is stuck (same mtime across multiple checks)
            current_mtime = os.path.getmtime(SCREENSHOT_PATH)
            if self.last_screenshot_time == current_mtime:
                self.consecutive_failures += 1
                logger.warning(
                    f"Screenshot unchanged for {self.consecutive_failures} checks"
                )
            else:
                self.last_screenshot_time = current_mtime
                self.consecutive_failures = 0

            if age_minutes > max_age:
                logger.warning(
                    f"Screenshot too old: {age_minutes:.1f} min (max {max_age:.0f} min)"
                )
                return False

            return True
        except Exception as e:
            logger.error(f"Screenshot check failed: {e}")
            return False

    def check_process_and_resources(self):
        """Combined check: process health + system resources in single pass.

        Returns (process_ok, resources_ok) to avoid iterating all processes twice.
        """
        try:
            main_process_found = False
            main_process_healthy = True
            browser_count = 0

            for proc in psutil.process_iter(["pid", "name", "cmdline", "status"]):
                try:
                    name = proc.info.get("name", "").lower()
                    cmdline = " ".join(proc.info.get("cmdline") or [])

                    # Check for main process
                    if "eink_display.py" in cmdline:
                        main_process_found = True

                        # Check for zombie/dead state
                        if proc.info["status"] == psutil.STATUS_ZOMBIE:
                            logger.error("Main process is a zombie")
                            main_process_healthy = False
                        elif proc.info["status"] == "disk-sleep":
                            logger.error("Main process in D state (uninterruptible)")
                            main_process_healthy = False
                        else:
                            # Check memory usage
                            memory_mb = proc.memory_info().rss / (1024 * 1024)
                            if memory_mb > MAX_MEMORY_MB:
                                logger.warning(
                                    f"Process using too much memory: {memory_mb:.1f}MB"
                                )
                                self.frozen_indicators.add("high_memory")

                            # Check CPU usage (stuck in busy loop?)
                            cpu_percent = proc.cpu_percent(interval=1)
                            if cpu_percent > 90:
                                logger.warning(
                                    f"Process using high CPU: {cpu_percent:.1f}%"
                                )
                                self.frozen_indicators.add("high_cpu")

                    # Count browser processes
                    if "chromium" in name or "chrome" in name:
                        browser_count += 1

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Evaluate process health
            if not main_process_found:
                logger.warning("Main process not found")
                process_ok = False
            elif not main_process_healthy:
                process_ok = False
            else:
                process_ok = len(self.frozen_indicators) < 2

            # Check browser leaks
            if browser_count > 3:
                logger.warning(f"Too many browser processes: {browser_count}")
                self.frozen_indicators.add("browser_leak")

            # System-level checks (no process iteration needed)
            memory = psutil.virtual_memory()
            available_mb = memory.available / (1024 * 1024)
            if available_mb < MIN_FREE_MEMORY_MB:
                logger.warning(f"Low system memory: {available_mb:.0f}MB available")
                self.frozen_indicators.add("low_memory")

            load_avg = os.getloadavg()[0]
            if load_avg > MAX_LOAD_AVG:
                logger.warning(f"High system load: {load_avg:.2f}")
                self.frozen_indicators.add("high_load")

            resources_ok = len(self.frozen_indicators) < 3

            return process_ok, resources_ok

        except Exception as e:
            logger.error(f"Combined health check failed: {e}")
            return True, True  # Assume OK if can't check

    def check_log_activity(self) -> bool:
        """Check if logs are still being written."""
        try:
            if not os.path.exists(LOG_PATH):
                return True  # Log might not exist yet

            # Check last modification time
            age_seconds = time.time() - os.path.getmtime(LOG_PATH)
            max_age = self.thresholds["log_inactivity_seconds"]
            if age_seconds > max_age:
                logger.warning(
                    f"No log activity for {age_seconds:.0f}s (max {max_age}s)"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"Log check failed: {e}")
            return True

    def _check_reboot_escalation(self):
        """Check if we should escalate to a full system reboot."""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.reboot_window_seconds)

        # Prune old timestamps
        self.restart_timestamps = [ts for ts in self.restart_timestamps if ts > cutoff]

        if len(self.restart_timestamps) >= self.max_restarts_before_reboot:
            logger.critical(
                f"System reboot: {len(self.restart_timestamps)} restarts "
                f"within {self.reboot_window_seconds // 60} minutes"
            )
            try:
                subprocess.run(["sudo", "reboot"], timeout=10, check=False)
            except Exception as e:
                logger.error(f"Reboot command failed: {e}")
            return True
        return False

    def force_restart(self, reason: str):
        """Restart the display service using systemctl restart."""
        # Track restart and check if we should escalate to reboot
        self.restart_timestamps.append(datetime.now())
        if self._check_reboot_escalation():
            return  # Reboot initiated

        logger.error(f"FORCE RESTART: {reason}")

        try:
            # Use systemctl restart (allowed by sudoers) instead of
            # stop/kill/start which requires permissions we don't have
            logger.info("Restarting display service...")
            result = subprocess.run(
                ["sudo", "systemctl", "restart", SERVICE_NAME],
                timeout=30,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                logger.info("Service restarted successfully")
            else:
                logger.error(
                    f"Service restart failed (exit {result.returncode}): "
                    f"{result.stderr.strip()}"
                )

            self.last_restart = datetime.now()
            self.consecutive_failures = 0
            self.frozen_indicators.clear()

            # Reset grace period so we don't immediately flag the restarted service
            self.startup_time = time.time()

            # Wait for service to stabilize
            time.sleep(30)

        except subprocess.TimeoutExpired:
            logger.error("Service restart timed out")
        except Exception as e:
            logger.error(f"Force restart failed: {e}")
            logger.critical("Unable to restart service, manual intervention needed")

    def run_checks(self) -> bool:
        """Run all health checks."""
        in_grace = self._in_grace_period()

        # During grace period, only check process health and system resources
        if in_grace:
            process_ok, resources_ok = self.check_process_and_resources()
            if not process_ok:
                logger.warning("Process unhealthy during grace period")
                return False
            if not resources_ok:
                logger.warning("Resources unhealthy during grace period")
                return False
            return True

        # Normal operation: run all checks
        checks = {
            "heartbeat": self.check_heartbeat(),
            "screenshot": self.check_screenshot_age(),
            "logs": self.check_log_activity(),
        }

        # Combined process + resource check (single process iteration pass)
        process_ok, resources_ok = self.check_process_and_resources()
        checks["process"] = process_ok
        checks["resources"] = resources_ok

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
        thresholds = self.thresholds
        logger.info("=" * 60)
        logger.info(f"Watchdog Monitor Started for {SERVICE_NAME}")
        logger.info(f"Refresh interval: {self.refresh_interval}s")
        logger.info(
            f"Screenshot: {SCREENSHOT_PATH} "
            f"(max {thresholds['max_screenshot_age_minutes']:.0f} min)"
        )
        logger.info(
            f"Heartbeat: {HEARTBEAT_PATH} "
            f"(max {thresholds['max_heartbeat_age_seconds']}s)"
        )
        logger.info(f"Log inactivity: max {thresholds['log_inactivity_seconds']}s")
        logger.info(f"Startup grace period: {thresholds['startup_grace_seconds']}s")
        logger.info(f"Check interval: {CHECK_INTERVAL}s")
        logger.info(
            f"Reboot escalation: after {self.max_restarts_before_reboot} restarts "
            f"within {self.reboot_window_seconds // 60} minutes"
        )
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
    watchdog = WatchdogMonitor()
    watchdog.run()
