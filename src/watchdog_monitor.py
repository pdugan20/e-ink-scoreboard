#!/usr/bin/env python3
"""
External watchdog monitor that ensures the display service is actually updating.
Runs as a separate process to detect and recover from kernel-level hangs.
"""

import logging
import os
import subprocess
import time
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
SCREENSHOT_PATH = "/tmp/sports_display.png"
MAX_AGE_MINUTES = 10  # Restart if screenshot older than this
CHECK_INTERVAL = 60  # Check every minute
SERVICE_NAME = "sports-display.service"


def get_file_age_minutes(filepath):
    """Get age of file in minutes."""
    try:
        if not os.path.exists(filepath):
            return float("inf")

        file_time = os.path.getmtime(filepath)
        current_time = time.time()
        age_seconds = current_time - file_time
        return age_seconds / 60
    except Exception as e:
        logger.error(f"Error checking file age: {e}")
        return float("inf")


def restart_service():
    """Restart the display service."""
    try:
        logger.warning(f"Screenshot is stale, restarting {SERVICE_NAME}...")

        # Try graceful restart first
        subprocess.run(["sudo", "systemctl", "restart", SERVICE_NAME], timeout=30)
        logger.info("Service restarted successfully")

        # Wait for service to start
        time.sleep(30)
        return True

    except subprocess.TimeoutExpired:
        logger.error("Service restart timed out, forcing kill...")

        # Force kill Python processes
        subprocess.run(["sudo", "pkill", "-9", "-f", "eink_display.py"], timeout=5)
        subprocess.run(["sudo", "pkill", "-9", "-f", "playwright"], timeout=5)

        # Start service again
        subprocess.run(["sudo", "systemctl", "start", SERVICE_NAME], timeout=30)
        return True

    except Exception as e:
        logger.error(f"Failed to restart service: {e}")
        return False


def check_process_state():
    """Check if main process is in D (uninterruptible) state."""
    try:
        result = subprocess.run(
            ["ps", "aux"], capture_output=True, text=True, timeout=5
        )

        for line in result.stdout.splitlines():
            if "eink_display.py" in line and " D" in line:
                logger.warning(
                    "Main process is in D (uninterruptible) state - likely frozen"
                )
                return False

        return True

    except Exception as e:
        logger.error(f"Error checking process state: {e}")
        return True  # Assume OK if can't check


def main():
    """Main watchdog loop."""
    logger.info(f"Starting watchdog monitor for {SERVICE_NAME}")
    logger.info(f"Monitoring {SCREENSHOT_PATH} (max age: {MAX_AGE_MINUTES} minutes)")

    last_restart = datetime.now() - timedelta(hours=1)  # Allow immediate restart

    while True:
        try:
            # Check screenshot age
            age_minutes = get_file_age_minutes(SCREENSHOT_PATH)

            if age_minutes > MAX_AGE_MINUTES:
                logger.warning(
                    f"Screenshot is {age_minutes:.1f} minutes old (threshold: {MAX_AGE_MINUTES})"
                )

                # Check if we recently restarted
                time_since_restart = datetime.now() - last_restart
                if time_since_restart.total_seconds() < 300:  # 5 minutes
                    logger.info("Recently restarted, waiting before another restart...")
                else:
                    # Check if process is frozen
                    if not check_process_state():
                        logger.error("Process appears frozen, forcing restart")
                        restart_service()
                        last_restart = datetime.now()
                    else:
                        logger.info("Process seems OK, will wait longer")
            else:
                logger.debug(f"Screenshot age OK: {age_minutes:.1f} minutes")

            # Sleep before next check
            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            logger.info("Watchdog monitor stopped by user")
            break
        except Exception as e:
            logger.error(f"Watchdog error: {e}")
            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
