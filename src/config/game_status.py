"""
Shared game status configuration loader.

Used by both the web API (dev_server.py) and display controller (game_checker.py).
"""

import json
import logging
import os

logger = logging.getLogger(__name__)

_config_cache = None


def load_game_status_config():
    """Load game status patterns from JSON config."""
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    try:
        config_path = os.path.join(os.path.dirname(__file__), "game-status-config.json")
        with open(config_path) as f:
            _config_cache = json.load(f)
            return _config_cache
    except Exception as e:
        logger.error(f"Could not load game status config: {e}")
        raise


def check_all_games_final(games):
    """Check if all games in a list have final status.

    Returns False for empty games list (no games != all games final).
    """
    if not games:
        return False

    status_config = load_game_status_config()
    final_statuses = status_config["finalGameStatuses"]

    return all(
        any(kw in game.get("status", "").lower() for kw in final_statuses)
        for game in games
    )
