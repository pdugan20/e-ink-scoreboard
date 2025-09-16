"""
Refresh logic and timing for e-ink display controller.
"""

import logging
import time
from datetime import datetime, timedelta

import requests

from utils.logging_config import log_resource_snapshot

logger = logging.getLogger(__name__)


class RefreshController:
    """Handles the refresh timing and decision logic for e-ink display."""

    def __init__(self, config, game_checker, screenshot_controller):
        self.config = config
        self.game_checker = game_checker
        self.screenshot_controller = screenshot_controller

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
            has_active_games = self.game_checker.check_active_games()
            if not has_active_games:
                logger.info("No active games found - skipping display update")
                return True  # Return success but skip display update

        # Take screenshot with retries
        screenshot_success = False
        for attempt in range(self.config["max_retries"]):
            if self.screenshot_controller.take_screenshot():
                screenshot_success = True
                break
            else:
                if attempt < self.config["max_retries"] - 1:
                    logger.warning(
                        f"Screenshot attempt {attempt + 1} failed, retrying..."
                    )
                    time.sleep(self.config["retry_delay"])

        if not screenshot_success:
            logger.error("Failed to take screenshot after all retries")
            return False

        # Process image
        img = self.screenshot_controller.process_image()
        if not img:
            return False

        # Update display
        return self.screenshot_controller.update_display(img)

    def run_continuous(self, wait_for_server_callback):
        """Run continuous refresh loop with smart game detection and screensaver refresh"""
        logger.info(
            f"Starting continuous refresh every {self.config['refresh_interval']} seconds"
        )

        if not wait_for_server_callback():
            return False

        last_game_date = None
        new_games_detected = False
        last_screensaver_hour = None

        while True:
            try:
                # Check current game date
                current_date = datetime.now().strftime("%Y-%m-%d")
                current_hour = datetime.now().hour

                # Force update if it's a new day
                force_update = False
                if last_game_date != current_date:
                    logger.info(f"New game day detected: {current_date}")
                    last_game_date = current_date
                    new_games_detected = False
                    last_screensaver_hour = None  # Reset screensaver hour tracking
                    force_update = True

                # Get consistent game state to prevent race conditions during transitions
                game_state = self.game_checker.get_game_state()
                has_active_games = game_state["has_active_games"]
                has_any_games = game_state["has_any_games"]
                screensaver_eligible = False  # Initialize here to avoid scope issues

                if has_any_games:
                    # There are games today (active, final, or scheduled) - show game scoreboard
                    # Only update if there are active games OR it's a forced update (new day)
                    if has_active_games or force_update:
                        success = self.refresh_display(force_update=force_update)
                        last_screensaver_hour = (
                            None  # Reset since we're not in screensaver mode
                        )

                        if success and not force_update:
                            logger.info(f"Checked for active games at {datetime.now()}")
                        elif success and force_update:
                            logger.info(f"Display updated at {datetime.now()}")
                        else:
                            logger.error("Display refresh failed")
                    else:
                        # No active games - check if there are still scheduled games
                        scheduled_games = game_state.get("scheduled_games", [])
                        final_games = game_state.get("final_games", [])

                        if scheduled_games:
                            # Games are scheduled but haven't started yet - keep checking
                            logger.info(
                                f"No active games, but {len(scheduled_games)} scheduled games pending. "
                                f"Continuing regular checks."
                            )
                        elif final_games and not scheduled_games:
                            # All games are final and no more scheduled - wait until next day
                            logger.info(
                                "All games finished for today, display staying static until next day"
                            )
                            # Calculate time until midnight (next day)
                            now = datetime.now()
                            tomorrow = datetime(
                                now.year, now.month, now.day
                            ) + timedelta(days=1)
                            seconds_until_tomorrow = (tomorrow - now).total_seconds()
                            # Add a small buffer (1 minute) to ensure we're past midnight
                            sleep_seconds = seconds_until_tomorrow + 60
                            logger.info(
                                f"Sleeping for {sleep_seconds/3600:.1f} hours until next day ({tomorrow.strftime('%Y-%m-%d %H:%M:%S')})"
                            )
                            time.sleep(sleep_seconds)
                            continue  # Skip the regular sleep interval and restart the loop
                        else:
                            # Edge case: games exist but no clear status
                            logger.info(
                                "Games exist but status unclear, continuing regular checks"
                            )

                else:
                    # No active games - check if screensaver is eligible
                    screensaver_eligible = (
                        self.game_checker.check_screensaver_eligible()
                    )

                    if screensaver_eligible:
                        # Screensaver mode - refresh every hour with new story
                        should_update_screensaver = (
                            force_update
                            or last_screensaver_hour is None
                            or current_hour != last_screensaver_hour
                        )

                        if should_update_screensaver:
                            logger.info("Refreshing screensaver with new article")
                            success = self.refresh_display(force_update=True)
                            if success:
                                last_screensaver_hour = current_hour
                                logger.info(
                                    f"Screensaver updated at {datetime.now()}, next refresh at hour {(current_hour + 1) % 24}"
                                )
                            else:
                                logger.error("Screensaver refresh failed")
                        else:
                            logger.debug(
                                f"Screensaver active, next refresh at hour {(current_hour + 1) % 24}"
                            )

                    else:
                        # No screensaver available - only update on new day (original behavior)
                        if force_update:
                            success = self.refresh_display(force_update=True)
                            if success:
                                logger.info(
                                    f"No-games display updated at {datetime.now()}"
                                )
                            else:
                                logger.error("No-games display update failed")
                        else:
                            logger.debug(
                                "No games, no screensaver - waiting for next day"
                            )

                # Check for scheduled games that might have started (use cached game state)
                if not force_update and not screensaver_eligible:
                    scheduled_games = game_state["scheduled_games"]

                    # If we have scheduled games and haven't detected new games yet, update once
                    if scheduled_games and not new_games_detected:
                        logger.info(
                            f"Found {len(scheduled_games)} scheduled games - updating display once for new day"
                        )
                        new_games_detected = True
                        success = self.refresh_display(force_update=True)

                logger.debug(f"Next check in {self.config['refresh_interval']} seconds")

                # Log resource usage every hour
                if datetime.now().minute == 0:
                    log_resource_snapshot(logger, "HOURLY_CHECK")

                time.sleep(int(self.config["refresh_interval"]))

            except KeyboardInterrupt:
                logger.info("Shutting down...")
                break
            except (requests.exceptions.RequestException, TimeoutError) as e:
                logger.warning(f"Network/timeout error (will retry): {e}")
                log_resource_snapshot(logger, "NETWORK_ERROR")
                time.sleep(
                    min(self.config["retry_delay"] * 2, 30)
                )  # Backoff with max 30s
            except MemoryError as e:
                logger.critical(
                    f"Memory error detected - system may be low on RAM: {e}"
                )
                log_resource_snapshot(logger, "MEMORY_ERROR")
                # Force garbage collection and wait longer
                import gc

                gc.collect()
                time.sleep(
                    min(self.config["retry_delay"] * 5, 120)
                )  # Longer backoff for memory issues
            except Exception as e:
                logger.error(f"Unexpected error in refresh loop: {e}")
                log_resource_snapshot(logger, "UNEXPECTED_ERROR")
                # Try to continue with a longer delay to prevent tight error loops
                time.sleep(min(self.config["retry_delay"] * 3, 60))  # Longer backoff
