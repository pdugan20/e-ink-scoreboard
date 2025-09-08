"""
Sports scores API endpoints for fetching live game data.
"""

import logging
from datetime import datetime, timedelta

import requests

logger = logging.getLogger(__name__)

MLB_API_BASE = "https://statsapi.mlb.com/api/v1"
NFL_API_BASE = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"


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
        for record in data.get("records", []):
            for team in record.get("teamRecords", []):
                team_name = team.get("team", {}).get("name", "")
                wins = team.get("wins", 0)
                losses = team.get("losses", 0)
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

        today = datetime.now().strftime("%Y-%m-%d")
        url = f"{MLB_API_BASE}/schedule/games/?sportId=1&date={today}&hydrate=linescore"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        games = []
        for date_data in data.get("dates", []):
            for game in date_data.get("games", []):
                # Get team names first
                away_team = (
                    game.get("teams", {})
                    .get("away", {})
                    .get("team", {})
                    .get("name", "")
                )
                home_team = (
                    game.get("teams", {})
                    .get("home", {})
                    .get("team", {})
                    .get("name", "")
                )

                # Determine game status
                status = game.get("status", {}).get("detailedState", "")
                if "In Progress" in status:
                    linescore = game.get("linescore", {})
                    inning_ordinal = linescore.get("currentInningOrdinal")
                    inning_state = linescore.get("inningState")

                    if inning_ordinal and inning_state:
                        status = f"{inning_state} {inning_ordinal}"
                    else:
                        status = "In Progress"
                elif status == "Scheduled" or status == "Pre-Game":
                    game_time_utc = datetime.fromisoformat(
                        game.get("gameDate", "").replace("Z", "+00:00")
                    )
                    # Convert UTC to ET (UTC-4 during daylight time, UTC-5 during standard time)
                    # For simplicity, we'll assume daylight time (EDT = UTC-4)
                    et_time = game_time_utc.replace(tzinfo=None) - timedelta(hours=4)
                    status = et_time.strftime("%-I:%M %p ET")

                # Get venue information
                venue_name = game.get("venue", {}).get("name", "")

                game_info = {
                    "away_team": away_team,
                    "home_team": home_team,
                    "away_score": game.get("teams", {}).get("away", {}).get("score", 0),
                    "home_score": game.get("teams", {}).get("home", {}).get("score", 0),
                    "away_record": standings.get(away_team, ""),
                    "home_record": standings.get(home_team, ""),
                    "status": status,
                    "venue": venue_name if venue_name else None,
                }

                # Add bases and outs data for in-progress games
                if "In Progress" in game.get("status", {}).get("detailedState", ""):
                    linescore = game.get("linescore", {})
                    offense = linescore.get("offense", {})

                    game_info["bases"] = {
                        "first": offense.get("first") is not None,
                        "second": offense.get("second") is not None,
                        "third": offense.get("third") is not None,
                    }
                    game_info["outs"] = linescore.get("outs", 0)
                games.append(game_info)

        # If no games today, try yesterday
        if not games:
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            url = f"{MLB_API_BASE}/schedule/games/?sportId=1&date={yesterday}"
            response = requests.get(url, timeout=10)
            data = response.json()

            for date_data in data.get("dates", []):
                for game in date_data.get("games", [])[:6]:  # Limit to 6 games
                    away_team = (
                        game.get("teams", {})
                        .get("away", {})
                        .get("team", {})
                        .get("name", "")
                    )
                    home_team = (
                        game.get("teams", {})
                        .get("home", {})
                        .get("team", {})
                        .get("name", "")
                    )

                    game_info = {
                        "away_team": away_team,
                        "home_team": home_team,
                        "away_score": game.get("teams", {})
                        .get("away", {})
                        .get("score", 0),
                        "home_score": game.get("teams", {})
                        .get("home", {})
                        .get("score", 0),
                        "away_record": standings.get(away_team, ""),
                        "home_record": standings.get(home_team, ""),
                        "status": "Final",
                    }
                    games.append(game_info)

        return games  # Return all games

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
        for event in data.get("events", [])[:6]:  # Limit to 6 games
            competition = event.get("competitions", [{}])[0]
            competitors = competition.get("competitors", [])

            if len(competitors) >= 2:
                home_team = next(
                    (c for c in competitors if c.get("homeAway") == "home"), {}
                )
                away_team = next(
                    (c for c in competitors if c.get("homeAway") == "away"), {}
                )

                # Determine game status
                status_detail = (
                    event.get("status", {}).get("type", {}).get("description", "")
                )
                if status_detail == "In Progress":
                    quarter = competition.get("status", {}).get("period", 0)
                    clock = competition.get("status", {}).get("displayClock", "")
                    status = f"Q{quarter} {clock}"
                elif status_detail == "Scheduled":
                    game_time = datetime.fromisoformat(
                        event.get("date", "").replace("Z", "+00:00")
                    )
                    status = game_time.strftime("%-I:%M %p ET")
                else:
                    status = status_detail

                game_info = {
                    "away_team": away_team.get("team", {}).get("displayName", ""),
                    "home_team": home_team.get("team", {}).get("displayName", ""),
                    "away_score": int(away_team.get("score", 0)),
                    "home_score": int(home_team.get("score", 0)),
                    "status": status,
                }
                games.append(game_info)

        return games

    except Exception as e:
        logger.error(f"Error fetching NFL games: {e}")
        return []
