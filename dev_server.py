#!/usr/bin/env python3
"""
Development server with hot reloading for testing sports scores display
Run with: python dev_server_hot.py
Then open: http://localhost:5000
"""

from flask import Flask, jsonify, send_from_directory, Response
from flask_cors import CORS
import requests
from datetime import datetime, timedelta
import logging
import os
import time
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for development

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MLB_API_BASE = "https://statsapi.mlb.com/api/v1"
NFL_API_BASE = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"

# Track file modification times for hot reload
file_timestamps = {}

def get_file_timestamp(filepath):
    try:
        return os.path.getmtime(filepath)
    except OSError:
        return 0

def get_files_to_watch():
    """Get all files to watch using glob patterns"""
    import glob
    
    patterns = [
        'preview.html',
        'static/styles/*.css',
        'static/js/*.js',
        'static/js/constants/*.js'
    ]
    
    files = []
    for pattern in patterns:
        files.extend(glob.glob(pattern))
    
    return files

def check_files_changed():
    """Check if any watched files have changed"""
    files_to_watch = get_files_to_watch()
    changed = False
    
    for filepath in files_to_watch:
        if os.path.exists(filepath):
            current_time = get_file_timestamp(filepath)
            last_time = file_timestamps.get(filepath, 0)
            
            if current_time > last_time:
                file_timestamps[filepath] = current_time
                changed = True
                logger.info(f"File changed: {filepath}")
    
    return changed

@app.route('/')
def index():
    """Serve the preview HTML with hot reload script injected"""
    try:
        with open('preview.html', 'r') as f:
            html_content = f.read()
        
        # Inject hot reload script
        hot_reload_script = """
        <script>
        // Hot reload functionality
        let reloadIndicator = null;
        
        function showReloadIndicator(message, isError = false) {
            if (!reloadIndicator) {
                reloadIndicator = document.createElement('div');
                reloadIndicator.className = 'reload-indicator';
                document.body.appendChild(reloadIndicator);
            }
            reloadIndicator.textContent = message;
            reloadIndicator.className = 'reload-indicator show' + (isError ? ' error' : '');
            setTimeout(() => {
                if (reloadIndicator) reloadIndicator.classList.remove('show');
            }, 2000);
        }
        
        function checkForUpdates() {
            fetch('/check-updates')
                .then(response => response.json())
                .then(data => {
                    if (data.changed) {
                        showReloadIndicator('Reloading...', false);
                        setTimeout(() => location.reload(), 500);
                    }
                })
                .catch(err => {
                    console.log('Hot reload check failed:', err);
                });
        }
        
        // Check for updates every 1 second
        setInterval(checkForUpdates, 1000);
        
        // Show indicator on initial load
        document.addEventListener('DOMContentLoaded', () => {
            showReloadIndicator('Hot reload active', false);
        });
        </script>
        """
        
        # Insert before closing </body> tag
        html_content = html_content.replace('</body>', hot_reload_script + '</body>')
        
        return html_content
    except FileNotFoundError:
        return "preview.html not found", 404

@app.route('/check-updates')
def check_updates():
    """Endpoint to check if files have changed"""
    changed = check_files_changed()
    return jsonify({'changed': changed})

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

@app.route('/static/test-data/<filename>')
def test_data_files(filename):
    """Serve test data files"""
    return send_from_directory('test-data', filename)

@app.route('/assets/<path:filename>')
def asset_files(filename):
    """Serve asset files (logos, etc.)"""
    return send_from_directory('assets', filename)

@app.route('/api/scores/<league>')
def get_scores(league):
    """Fetch live scores for the specified league"""
    try:
        if league == 'MLB':
            return jsonify(fetch_mlb_games())
        elif league == 'NFL':
            return jsonify(fetch_nfl_games())
        else:
            return jsonify({'error': 'Invalid league'}), 400
    except Exception as e:
        logger.error(f"Error fetching scores: {e}")
        return jsonify({'error': str(e)}), 500

def fetch_mlb_standings():
    """Fetch current MLB standings"""
    try:
        # Use current year for standings
        current_year = datetime.now().year
        url = f"{MLB_API_BASE}/standings?leagueId=103,104&season={current_year}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        standings = {}
        for record in data.get('records', []):
            for team in record.get('teamRecords', []):
                team_name = team.get('team', {}).get('name', '')
                wins = team.get('wins', 0)
                losses = team.get('losses', 0)
                standings[team_name] = f"{wins}-{losses}"
        
        return standings
    except Exception as e:
        logger.error(f"Error fetching MLB standings: {e}")
        return {}

def fetch_mlb_games():
    """Fetch MLB games for today"""
    try:
        # Get standings data
        standings = fetch_mlb_standings()
        
        today = datetime.now().strftime('%Y-%m-%d')
        url = f"{MLB_API_BASE}/schedule/games/?sportId=1&date={today}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        games = []
        for date_data in data.get('dates', []):
            for game in date_data.get('games', []):
                # Determine game status
                status = game.get('status', {}).get('detailedState', '')
                if 'In Progress' in status:
                    inning = game.get('linescore', {}).get('currentInning', 0)
                    inning_state = game.get('linescore', {}).get('inningState', '')
                    status = f"{inning_state} {inning}"
                elif status == 'Scheduled' or status == 'Pre-Game':
                    game_time_utc = datetime.fromisoformat(game.get('gameDate', '').replace('Z', '+00:00'))
                    # Convert UTC to ET (UTC-4 during daylight time, UTC-5 during standard time)
                    # For simplicity, we'll assume daylight time (EDT = UTC-4)
                    et_time = game_time_utc.replace(tzinfo=None) - timedelta(hours=4)
                    status = et_time.strftime('%-I:%M %p ET')
                
                away_team = game.get('teams', {}).get('away', {}).get('team', {}).get('name', '')
                home_team = game.get('teams', {}).get('home', {}).get('team', {}).get('name', '')
                
                game_info = {
                    'away_team': away_team,
                    'home_team': home_team,
                    'away_score': game.get('teams', {}).get('away', {}).get('score', 0),
                    'home_score': game.get('teams', {}).get('home', {}).get('score', 0),
                    'away_record': standings.get(away_team, ''),
                    'home_record': standings.get(home_team, ''),
                    'status': status
                }
                games.append(game_info)
        
        # If no games today, try yesterday
        if not games:
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            url = f"{MLB_API_BASE}/schedule/games/?sportId=1&date={yesterday}"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            for date_data in data.get('dates', []):
                for game in date_data.get('games', [])[:6]:  # Limit to 6 games
                    away_team = game.get('teams', {}).get('away', {}).get('team', {}).get('name', '')
                    home_team = game.get('teams', {}).get('home', {}).get('team', {}).get('name', '')
                    
                    game_info = {
                        'away_team': away_team,
                        'home_team': home_team,
                        'away_score': game.get('teams', {}).get('away', {}).get('score', 0),
                        'home_score': game.get('teams', {}).get('home', {}).get('score', 0),
                        'away_record': standings.get(away_team, ''),
                        'home_record': standings.get(home_team, ''),
                        'status': 'Final'
                    }
                    games.append(game_info)
        
        return games[:6]  # Return max 6 games
        
    except Exception as e:
        logger.error(f"Error fetching MLB games: {e}")
        return []

def fetch_nfl_games():
    """Fetch NFL games for current week"""
    try:
        url = f"{NFL_API_BASE}/scoreboard"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        games = []
        for event in data.get('events', [])[:6]:  # Limit to 6 games
            competition = event.get('competitions', [{}])[0]
            competitors = competition.get('competitors', [])
            
            if len(competitors) >= 2:
                home_team = next((c for c in competitors if c.get('homeAway') == 'home'), {})
                away_team = next((c for c in competitors if c.get('homeAway') == 'away'), {})
                
                # Determine game status
                status_detail = event.get('status', {}).get('type', {}).get('description', '')
                if status_detail == 'In Progress':
                    quarter = competition.get('status', {}).get('period', 0)
                    clock = competition.get('status', {}).get('displayClock', '')
                    status = f"Q{quarter} {clock}"
                elif status_detail == 'Scheduled':
                    game_time = datetime.fromisoformat(event.get('date', '').replace('Z', '+00:00'))
                    status = game_time.strftime('%-I:%M %p ET')
                else:
                    status = status_detail
                
                game_info = {
                    'away_team': away_team.get('team', {}).get('displayName', ''),
                    'home_team': home_team.get('team', {}).get('displayName', ''),
                    'away_score': int(away_team.get('score', 0)),
                    'home_score': int(home_team.get('score', 0)),
                    'status': status
                }
                games.append(game_info)
        
        return games
        
    except Exception as e:
        logger.error(f"Error fetching NFL games: {e}")
        return []

if __name__ == '__main__':
    # Initialize file timestamps
    for filepath in get_files_to_watch():
        if os.path.exists(filepath):
            file_timestamps[filepath] = get_file_timestamp(filepath)
    
    print("\n🏈 Sports Scores Dev Server (Hot Reload)")
    print("=" * 50)
    print("Open in browser: http://localhost:5001")
    print("API endpoints:")
    print("  - http://localhost:5001/api/scores/MLB")
    print("  - http://localhost:5001/api/scores/NFL")
    print("\n✨ Hot reload enabled:")
    print("  - Edit preview.html, CSS in static/styles/, or JS in static/js/")
    print("  - Browser will auto-refresh on save")
    print("=" * 50)
    print("\nPress Ctrl+C to stop\n")
    
    # Suppress werkzeug INFO logs for check-updates endpoint only
    import logging
    werkzeug_logger = logging.getLogger('werkzeug')
    
    class SuppressCheckUpdates(logging.Filter):
        def filter(self, record):
            return not ('GET /check-updates HTTP' in record.getMessage())
    
    werkzeug_logger.addFilter(SuppressCheckUpdates())
    
    app.run(debug=True, port=5001, use_reloader=False)  # Disable Flask's reloader since we have our own