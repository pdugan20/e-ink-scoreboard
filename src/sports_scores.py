import os
import json
import logging
from datetime import datetime, timedelta
from plugins.base_plugin.base_plugin import BasePlugin
from PIL import Image, ImageDraw, ImageFont
from utils.app_utils import get_font
import requests
import pytz

logger = logging.getLogger(__name__)

SPORTS_LEAGUES = [
    {"name": "MLB", "icon": "icons/mlb.png"},
    {"name": "NFL", "icon": "icons/nfl.png"}
]

DEFAULT_TIMEZONE = "US/Eastern"
DEFAULT_LEAGUE = "MLB"

class SportsScores(BasePlugin):
    def __init__(self, config, **dependencies):
        super().__init__(config, **dependencies)
        self.mlb_api_base = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb"
        self.nfl_api_base = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
        
    def generate_settings_template(self):
        template_params = super().generate_settings_template()
        template_params['sports_leagues'] = SPORTS_LEAGUES
        return template_params
    
    def generate_image(self, settings, device_config):
        selected_league = settings.get('selectedLeague', DEFAULT_LEAGUE)
        selected_team = settings.get('selectedTeam', '')
        show_standings = settings.get('showStandings', False)
        
        dimensions = device_config.get_resolution()
        if device_config.get_config("orientation") == "vertical":
            dimensions = dimensions[::-1]
            
        timezone_name = device_config.get_config("timezone") or DEFAULT_TIMEZONE
        tz = pytz.timezone(timezone_name)
        
        try:
            if selected_league == "MLB":
                return self.generate_mlb_scores(dimensions, selected_team, show_standings, tz)
            elif selected_league == "NFL":
                return self.generate_nfl_scores(dimensions, selected_team, show_standings, tz)
            else:
                raise RuntimeError(f"Unsupported league: {selected_league}")
        except Exception as e:
            logger.error(f"Failed to generate sports scores: {str(e)}")
            raise RuntimeError(f"Failed to display sports scores: {str(e)}")
    
    def fetch_mlb_games(self, date_str):
        """Fetch MLB games for a specific date"""
        try:
            url = f"{self.mlb_api_base}/scoreboard"
            if date_str:
                url += f"?dates={date_str}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            games = []
            for event in data.get('events', []):
                competition = event.get('competitions', [{}])[0]
                competitors = competition.get('competitors', [])
                venue = competition.get('venue', {})
                
                if len(competitors) >= 2:
                    home_team = next((c for c in competitors if c.get('homeAway') == 'home'), {})
                    away_team = next((c for c in competitors if c.get('homeAway') == 'away'), {})
                    
                    game_info = {
                        'game_id': event.get('id'),
                        'status': competition.get('status', {}).get('type', {}).get('description', ''),
                        'home_team': home_team.get('team', {}).get('displayName', ''),
                        'away_team': away_team.get('team', {}).get('displayName', ''),
                        'home_score': home_team.get('score', 0),
                        'away_score': away_team.get('score', 0),
                        'venue': venue.get('fullName', ''),
                        'game_date': event.get('date', '')
                    }
                    games.append(game_info)
            
            return games
        except Exception as e:
            logger.error(f"Error fetching MLB games: {e}")
            return []
    
    def fetch_nfl_games(self, week=None):
        """Fetch NFL games for current week or specified week"""
        try:
            url = f"{self.nfl_api_base}/scoreboard"
            if week:
                url += f"?week={week}"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            games = []
            for event in data.get('events', []):
                competition = event.get('competitions', [{}])[0]
                competitors = competition.get('competitors', [])
                
                if len(competitors) >= 2:
                    home_team = next((c for c in competitors if c.get('homeAway') == 'home'), {})
                    away_team = next((c for c in competitors if c.get('homeAway') == 'away'), {})
                    
                    game_info = {
                        'game_id': event.get('id'),
                        'status': event.get('status', {}).get('type', {}).get('description', ''),
                        'home_team': home_team.get('team', {}).get('displayName', ''),
                        'away_team': away_team.get('team', {}).get('displayName', ''),
                        'home_score': int(home_team.get('score', 0)),
                        'away_score': int(away_team.get('score', 0)),
                        'quarter': competition.get('status', {}).get('period', 0),
                        'clock': competition.get('status', {}).get('displayClock', ''),
                        'game_date': event.get('date', '')
                    }
                    games.append(game_info)
            
            return games
        except Exception as e:
            logger.error(f"Error fetching NFL games: {e}")
            return []
    
    def generate_mlb_scores(self, dimensions, selected_team, show_standings, tz):
        """Generate image with MLB scores"""
        width, height = dimensions
        
        # Create white background
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        # Fonts
        title_font = get_font("Roboto-Bold", int(height * 0.06))
        team_font = get_font("Roboto-Medium", int(height * 0.04))
        score_font = get_font("Roboto-Bold", int(height * 0.05))
        status_font = get_font("Roboto-Regular", int(height * 0.03))
        
        # Title
        draw.text((width // 2, int(height * 0.05)), "MLB Scores", 
                 font=title_font, fill='black', anchor='mt')
        
        # Get today's date
        today = datetime.now(tz)
        date_str = today.strftime('%Y-%m-%d')
        
        # Fetch games
        games = self.fetch_mlb_games(date_str)
        
        if not games:
            # Try yesterday's games
            yesterday = today - timedelta(days=1)
            date_str = yesterday.strftime('%Y-%m-%d')
            games = self.fetch_mlb_games(date_str)
            
        # Draw date
        draw.text((width // 2, int(height * 0.11)), date_str, 
                 font=status_font, fill='gray', anchor='mt')
        
        # Draw games
        y_offset = int(height * 0.18)
        game_height = int(height * 0.12)
        max_games = min(len(games), 6)  # Limit to 6 games to fit screen
        
        for i, game in enumerate(games[:max_games]):
            # Filter by team if selected
            if selected_team and selected_team not in [game['home_team'], game['away_team']]:
                continue
                
            # Game box
            box_y = y_offset + (i * game_height)
            
            # Away team
            draw.text((int(width * 0.05), box_y), game['away_team'][:15], 
                     font=team_font, fill='black', anchor='lm')
            draw.text((int(width * 0.85), box_y), str(game['away_score']), 
                     font=score_font, fill='black', anchor='rm')
            
            # Home team
            draw.text((int(width * 0.05), box_y + int(game_height * 0.4)), 
                     game['home_team'][:15], 
                     font=team_font, fill='black', anchor='lm')
            draw.text((int(width * 0.85), box_y + int(game_height * 0.4)), 
                     str(game['home_score']), 
                     font=score_font, fill='black', anchor='rm')
            
            # Game status
            status_text = game['status']
            if 'In Progress' in status_text and game['inning']:
                status_text = f"{game['inning_state']} {game['inning']}"
            
            draw.text((width // 2, box_y + int(game_height * 0.7)), 
                     status_text, 
                     font=status_font, fill='gray', anchor='mt')
            
            # Divider line
            if i < max_games - 1:
                draw.line([(int(width * 0.05), box_y + game_height - 5), 
                          (int(width * 0.95), box_y + game_height - 5)], 
                         fill='lightgray', width=1)
        
        return img
    
    def generate_nfl_scores(self, dimensions, selected_team, show_standings, tz):
        """Generate image with NFL scores"""
        width, height = dimensions
        
        # Create white background
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        # Fonts
        title_font = get_font("Roboto-Bold", int(height * 0.06))
        team_font = get_font("Roboto-Medium", int(height * 0.04))
        score_font = get_font("Roboto-Bold", int(height * 0.05))
        status_font = get_font("Roboto-Regular", int(height * 0.03))
        
        # Title
        draw.text((width // 2, int(height * 0.05)), "NFL Scores", 
                 font=title_font, fill='black', anchor='mt')
        
        # Fetch games
        games = self.fetch_nfl_games()
        
        # Draw current week
        draw.text((width // 2, int(height * 0.11)), "Current Week", 
                 font=status_font, fill='gray', anchor='mt')
        
        # Draw games
        y_offset = int(height * 0.18)
        game_height = int(height * 0.12)
        max_games = min(len(games), 6)  # Limit to 6 games to fit screen
        
        for i, game in enumerate(games[:max_games]):
            # Filter by team if selected
            if selected_team and selected_team not in [game['home_team'], game['away_team']]:
                continue
                
            # Game box
            box_y = y_offset + (i * game_height)
            
            # Away team
            draw.text((int(width * 0.05), box_y), game['away_team'][:15], 
                     font=team_font, fill='black', anchor='lm')
            draw.text((int(width * 0.85), box_y), str(game['away_score']), 
                     font=score_font, fill='black', anchor='rm')
            
            # Home team
            draw.text((int(width * 0.05), box_y + int(game_height * 0.4)), 
                     game['home_team'][:15], 
                     font=team_font, fill='black', anchor='lm')
            draw.text((int(width * 0.85), box_y + int(game_height * 0.4)), 
                     str(game['home_score']), 
                     font=score_font, fill='black', anchor='rm')
            
            # Game status
            status_text = game['status']
            if game['quarter'] and game['clock']:
                status_text = f"Q{game['quarter']} {game['clock']}"
            
            draw.text((width // 2, box_y + int(game_height * 0.7)), 
                     status_text, 
                     font=status_font, fill='gray', anchor='mt')
            
            # Divider line
            if i < max_games - 1:
                draw.line([(int(width * 0.05), box_y + game_height - 5), 
                          (int(width * 0.95), box_y + game_height - 5)], 
                         fill='lightgray', width=1)
        
        return img