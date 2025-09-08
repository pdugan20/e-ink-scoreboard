"""
Game status checking logic for e-ink display controller.
"""

import json
import os
import logging
import requests

logger = logging.getLogger(__name__)


def load_game_status_config():
    """Load game status patterns from JSON config"""
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'game-status-config.json')
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Could not load game status config: {e}")
        raise


class GameChecker:
    """Handles checking game status and screensaver eligibility."""
    
    def __init__(self, web_server_url):
        self.web_server_url = web_server_url
        self.base_url = web_server_url.replace('/display', '')
    
    def check_active_games(self):
        """Check if there are any active games by fetching game data"""
        try:
            # Load game status config
            status_config = load_game_status_config()
            
            # Get game data via API
            api_url = f"{self.base_url}/api/scores/MLB"
            
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
            
            # Return True if there are active games
            return len(active_games) > 0
            
        except Exception as e:
            logger.error(f"Error checking active games: {e}")
            return True  # Default to updating if there's an error
    
    def check_any_games_today(self):
        """Check if there are ANY games today (active, final, or scheduled)"""
        try:
            # Get game data via API
            api_url = f"{self.base_url}/api/scores/MLB"
            
            response = requests.get(api_url, timeout=10)
            if response.status_code != 200:
                logger.warning(f"Could not fetch game data: {response.status_code}")
                return True  # Default to showing games if we can't check
            
            games = response.json()
            # Return True if there are any games at all (empty array means no games today)
            return bool(games and len(games) > 0)
            
        except Exception as e:
            logger.error(f"Error checking for any games today: {e}")
            return True  # Default to showing games if there's an error
    
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
            return data and data.get('title') and data.get('image_url')
            
        except Exception as e:
            logger.debug(f"Screensaver check failed: {e}")
            return False
    
    def check_scheduled_games(self):
        """Check for scheduled games that might have started"""
        try:
            api_url = f"{self.base_url}/api/scores/MLB"
            response = requests.get(api_url, timeout=10)
            
            if response.status_code == 200:
                games = response.json()
                scheduled_games = [g for g in games if any(kw in g.get('status', '').lower() 
                                 for kw in ['pm et', 'am et', 'scheduled'])]
                return scheduled_games
            return []
        except Exception as e:
            logger.warning(f"Error checking for scheduled games: {e}")
            return []