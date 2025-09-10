"""
Game status checking logic for e-ink display controller.
"""

import json
import logging
import os
import time

import requests

logger = logging.getLogger(__name__)


def load_game_status_config():
    """Load game status patterns from JSON config"""
    try:
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "config",
            "game-status-config.json",
        )
        with open(config_path) as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Could not load game status config: {e}")
        raise


class GameChecker:
    """Handles checking game status and screensaver eligibility."""

    def __init__(self, web_server_url):
        self.web_server_url = web_server_url
        self.base_url = web_server_url.replace("/display", "")
        self._last_game_state = None
        self._game_state_cache_time = 0
        self._api_failure_count = 0
        self._api_failure_threshold = 3
        self._circuit_open_until = 0

    def get_game_state(self):
        """Get game state with caching and circuit breaker to prevent race conditions."""
        current_time = time.time()

        # Cache game state for 30 seconds to prevent inconsistent reads during transitions
        if (
            self._last_game_state is not None
            and current_time - self._game_state_cache_time < 30
        ):
            return self._last_game_state

        # Circuit breaker: if we've had too many failures, use cached state for a while
        if current_time < self._circuit_open_until:
            logger.warning("API circuit breaker open, using cached game state")
            return self._last_game_state or {
                "has_active_games": True,
                "has_any_games": True,
                "games": [],
            }

        try:
            # Load game status config
            status_config = load_game_status_config()

            # Get game data via API (single call for consistency)
            api_url = f"{self.base_url}/api/scores/MLB"
            response = requests.get(api_url, timeout=5)

            if response.status_code != 200:
                self._handle_api_failure()
                logger.warning(f"Could not fetch game data: {response.status_code}")
                # Return cached state if available, otherwise default
                return self._last_game_state or {
                    "has_active_games": True,
                    "has_any_games": True,
                    "games": [],
                }

            # Reset failure count on success
            self._api_failure_count = 0

            games = response.json()

            # Analyze all games in one pass
            active_games = []
            scheduled_games = []
            final_games = []

            for game in games:
                status = game.get("status", "").lower()

                if any(
                    keyword in status for keyword in status_config["activeGameStatuses"]
                ):
                    active_games.append(game)
                elif any(
                    keyword in status
                    for keyword in status_config["scheduledGameStatuses"]
                ):
                    scheduled_games.append(game)
                elif any(
                    keyword in status for keyword in status_config["finalGameStatuses"]
                ):
                    final_games.append(game)
                else:
                    # Unknown status, treat as active to be safe
                    active_games.append(game)

            game_state = {
                "has_active_games": len(active_games) > 0,
                "has_any_games": len(games) > 0,
                "active_games": active_games,
                "scheduled_games": scheduled_games,
                "final_games": final_games,
                "games": games,
            }

            # Cache the result
            self._last_game_state = game_state
            self._game_state_cache_time = current_time

            logger.info(
                f"Game state: {len(active_games)} active, {len(scheduled_games)} scheduled, {len(final_games)} final"
            )

            return game_state

        except Exception as e:
            self._handle_api_failure()
            logger.error(f"Error getting game state: {e}")
            # Return cached state if available, otherwise safe default
            return self._last_game_state or {
                "has_active_games": True,
                "has_any_games": True,
                "games": [],
            }

    def _handle_api_failure(self):
        """Handle API failure with circuit breaker pattern."""
        self._api_failure_count += 1
        if self._api_failure_count >= self._api_failure_threshold:
            # Open circuit for 5 minutes
            self._circuit_open_until = time.time() + 300
            logger.warning(
                f"API circuit breaker opened after {self._api_failure_count} failures"
            )

    def check_active_games(self):
        """Check if there are any active games using cached game state."""
        game_state = self.get_game_state()
        return game_state["has_active_games"]

    def check_any_games_today(self):
        """Check if there are ANY games today using cached game state."""
        game_state = self.get_game_state()
        return game_state["has_any_games"]

    def check_screensaver_eligible(self):
        """Check if screensaver should be shown (no games available and RSS feed configured)"""
        try:
            # Check screensaver API
            api_url = f"{self.base_url}/api/screensaver/mlb"

            response = requests.get(api_url, timeout=10)
            if response.status_code != 200:
                return False

            data = response.json()
            # Screensaver is eligible if we got actual article data (not empty response)
            return data and data.get("title") and data.get("image_url")

        except Exception as e:
            logger.debug(f"Screensaver check failed: {e}")
            return False

    def check_scheduled_games(self):
        """Check for scheduled games using cached game state."""
        game_state = self.get_game_state()
        return game_state["scheduled_games"]
