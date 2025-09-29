"""
Game status checking logic for e-ink display controller.
"""

import json
import logging
import os
import time
from datetime import datetime

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
        self._last_cache_date = None  # Track the date of cached data

        # Create persistent session for connection pooling
        self._session = requests.Session()
        # Set reasonable timeouts and connection limits
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=2,  # Small pool for this application
            pool_maxsize=5,
            max_retries=requests.adapters.Retry(
                total=2, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504]
            ),
        )
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

    def _get_fallback_game_state(self, current_date):
        """Get fallback game state when API is unavailable or cache is stale."""
        # Don't use stale cache from previous day
        if self._last_game_state and self._last_cache_date == current_date:
            return self._last_game_state
        else:
            # Return safe default for new day when API is unavailable
            return {
                "has_active_games": False,
                "has_any_games": False,
                "games": [],
                "active_games": [],
                "scheduled_games": [],
                "final_games": [],
            }

    def get_game_state(self):
        """Get game state with caching and circuit breaker to prevent race conditions."""
        current_time = time.time()
        current_date = datetime.now().strftime("%Y-%m-%d")

        # Clear cache if it's a new day to prevent showing yesterday's games
        if self._last_cache_date and self._last_cache_date != current_date:
            logger.info(f"New day detected ({current_date}), clearing game state cache")
            self._last_game_state = None
            self._game_state_cache_time = 0
            self._last_cache_date = current_date

        # Cache game state for 30 seconds to prevent inconsistent reads during transitions
        if (
            self._last_game_state is not None
            and current_time - self._game_state_cache_time < 30
        ):
            return self._last_game_state

        # Circuit breaker: if we've had too many failures, use cached state for a while
        if current_time < self._circuit_open_until:
            logger.warning("API circuit breaker open, using cached game state")
            return self._get_fallback_game_state(current_date)

        try:
            # Load game status config
            status_config = load_game_status_config()

            # Get game data via API (single call for consistency)
            api_url = f"{self.base_url}/api/scores/MLB"
            response = self._session.get(api_url, timeout=5)

            if response.status_code != 200:
                self._handle_api_failure()
                logger.warning(f"Could not fetch game data: {response.status_code}")
                return self._get_fallback_game_state(current_date)

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
            self._last_cache_date = current_date  # Update cache date

            logger.info(
                f"Game state: {len(active_games)} active, {len(scheduled_games)} scheduled, {len(final_games)} final"
            )

            return game_state

        except Exception as e:
            self._handle_api_failure()
            logger.error(f"Error getting game state: {e}")
            return self._get_fallback_game_state(current_date)

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

            response = self._session.get(api_url, timeout=10)
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

    def cleanup(self):
        """Clean up resources (call on shutdown)."""
        try:
            self._session.close()
            logger.info("Game checker session closed")
        except Exception as e:
            logger.warning(f"Error closing game checker session: {e}")

    def __del__(self):
        """Cleanup on garbage collection."""
        self.cleanup()
