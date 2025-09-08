"""
Screensaver API endpoints for fetching team news content.
"""

import logging
import os
import re
import sys

logger = logging.getLogger(__name__)


def get_favorite_teams_from_config():
    """Parse the JavaScript config file to extract favorite teams"""
    try:
        # Path to the JavaScript config file
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "static", "js", "config.js"
        )

        with open(config_path) as f:
            config_content = f.read()

        # Extract the favoriteTeams object using regex
        # Look for: favoriteTeams = { ... };
        pattern = r"favoriteTeams\s*=\s*\{([^}]+)\}"
        match = re.search(pattern, config_content, re.DOTALL)

        if not match:
            logger.warning("Could not find favoriteTeams in config.js")
            return {}

        favorite_teams_content = match.group(1)

        # Parse each league's favorite teams
        favorite_teams = {}

        # Look for patterns like: mlb: ['Seattle Mariners'], or mlb: null,
        league_pattern = r"(\w+):\s*(\[[^\]]*\]|null)"
        for league_match in re.finditer(league_pattern, favorite_teams_content):
            league = league_match.group(1).strip()
            teams_str = league_match.group(2).strip()

            if teams_str == "null":
                favorite_teams[league] = []
            else:
                # Extract team names from array format like ['Seattle Mariners']
                team_pattern = r"'([^']+)'"
                teams = re.findall(team_pattern, teams_str)
                favorite_teams[league] = teams

        logger.info(f"Loaded favorite teams from config: {favorite_teams}")
        return favorite_teams

    except Exception as e:
        logger.error(f"Error parsing favorite teams from config: {e}")
        return {}


def get_screensaver_data(league):
    """Fetch screensaver article for favorite team in specified league"""
    try:
        # Import and initialize the screensaver service
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from services.screensaver_service import ScreensaverService

        screensaver_service = ScreensaverService()

        # Get favorite teams from the JavaScript config file
        favorite_teams_config = get_favorite_teams_from_config()
        favorite_teams = favorite_teams_config.get(league.lower(), [])

        if not favorite_teams:
            return {}

        # Fetch article for the favorite team
        article_data = screensaver_service.fetch_article_for_favorites(
            favorite_teams, league.lower()
        )

        return article_data

    except Exception as e:
        logger.error(f"Error fetching screensaver data for {league}: {e}")
        return {"error": str(e)}
