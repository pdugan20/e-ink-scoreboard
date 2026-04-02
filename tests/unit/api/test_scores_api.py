"""
Unit tests for scores API functions.

Tests the MLB and NFL API integration logic without making real HTTP requests.
"""

from datetime import datetime

import pytest
import requests

from src.api.scores_api import (
    MLB_API_BASE,
    NFL_API_BASE,
    fetch_mlb_games,
    fetch_mlb_standings,
    fetch_nfl_games,
)
from src.config.game_status import check_all_games_final


@pytest.mark.unit
class TestMLBStandings:
    """Tests for MLB standings fetching"""

    def test_fetch_mlb_standings_success(self, requests_mock):
        """Test that fetch_mlb_standings correctly parses API response"""
        # Arrange
        mock_response = {
            "records": [
                {
                    "teamRecords": [
                        {
                            "team": {"name": "New York Yankees"},
                            "wins": 95,
                            "losses": 67,
                        },
                        {
                            "team": {"name": "Boston Red Sox"},
                            "wins": 78,
                            "losses": 84,
                        },
                    ]
                }
            ]
        }

        current_year = datetime.now().year
        requests_mock.get(
            f"{MLB_API_BASE}/standings?leagueId=103,104&season={current_year}",
            json=mock_response,
        )

        # Act
        standings = fetch_mlb_standings()

        # Assert
        assert standings == {
            "New York Yankees": "95-67",
            "Boston Red Sox": "78-84",
        }

    def test_fetch_mlb_standings_empty_records(self, requests_mock):
        """Test handling of empty standings data"""
        # Arrange
        current_year = datetime.now().year
        requests_mock.get(
            f"{MLB_API_BASE}/standings?leagueId=103,104&season={current_year}",
            json={"records": []},
        )

        # Act
        standings = fetch_mlb_standings()

        # Assert
        assert standings == {}

    def test_fetch_mlb_standings_api_failure(self, requests_mock):
        """Test that standings API failure returns empty dict"""
        # Arrange
        current_year = datetime.now().year
        requests_mock.get(
            f"{MLB_API_BASE}/standings?leagueId=103,104&season={current_year}",
            status_code=500,
        )

        # Act
        standings = fetch_mlb_standings()

        # Assert
        assert standings == {}

    def test_fetch_mlb_standings_timeout(self, requests_mock):
        """Test that standings API timeout returns empty dict"""
        # Arrange
        current_year = datetime.now().year
        requests_mock.get(
            f"{MLB_API_BASE}/standings?leagueId=103,104&season={current_year}",
            exc=requests.exceptions.Timeout,
        )

        # Act
        standings = fetch_mlb_standings()

        # Assert
        assert standings == {}


@pytest.mark.unit
class TestMLBGames:
    """Tests for MLB games fetching"""

    def test_fetch_mlb_games_live_game(self, requests_mock):
        """Test parsing a live MLB game"""
        # Arrange - Mock standings
        standings_response = {
            "records": [
                {
                    "teamRecords": [
                        {
                            "team": {"name": "New York Yankees"},
                            "wins": 82,
                            "losses": 65,
                        },
                        {
                            "team": {"name": "Boston Red Sox"},
                            "wins": 78,
                            "losses": 69,
                        },
                    ]
                }
            ]
        }

        current_year = datetime.now().year
        requests_mock.get(
            f"{MLB_API_BASE}/standings?leagueId=103,104&season={current_year}",
            json=standings_response,
        )

        # Arrange - Mock games
        today = datetime.now().strftime("%Y-%m-%d")
        games_response = {
            "dates": [
                {
                    "games": [
                        {
                            "teams": {
                                "away": {
                                    "team": {"name": "New York Yankees"},
                                    "score": 5,
                                },
                                "home": {
                                    "team": {"name": "Boston Red Sox"},
                                    "score": 3,
                                },
                            },
                            "status": {"detailedState": "In Progress"},
                            "linescore": {
                                "currentInningOrdinal": "7th",
                                "inningState": "Top",
                                "outs": 2,
                                "offense": {
                                    "first": {"id": 123},
                                    "second": None,
                                    "third": {"id": 456},
                                },
                            },
                            "venue": {"name": "Fenway Park"},
                        }
                    ]
                }
            ]
        }

        requests_mock.get(
            f"{MLB_API_BASE}/schedule/games/?sportId=1&date={today}&hydrate=linescore",
            json=games_response,
        )

        # Act
        games = fetch_mlb_games()

        # Assert
        assert len(games) == 1
        game = games[0]
        assert game["away_team"] == "New York Yankees"
        assert game["home_team"] == "Boston Red Sox"
        assert game["away_score"] == 5
        assert game["home_score"] == 3
        assert game["away_record"] == "82-65"
        assert game["home_record"] == "78-69"
        assert game["status"] == "Top 7th"
        assert game["venue"] == "Fenway Park"
        assert game["bases"] == {"first": True, "second": False, "third": True}
        assert game["outs"] == 2

    def test_fetch_mlb_games_scheduled(self, requests_mock):
        """Test parsing a scheduled MLB game"""
        # Arrange - Mock standings
        current_year = datetime.now().year
        requests_mock.get(
            f"{MLB_API_BASE}/standings?leagueId=103,104&season={current_year}",
            json={"records": []},
        )

        # Arrange - Mock scheduled game
        today = datetime.now().strftime("%Y-%m-%d")
        game_time = "2024-09-15T19:05:00Z"  # 7:05 PM ET (3:05 PM ET after -4 hours)

        games_response = {
            "dates": [
                {
                    "games": [
                        {
                            "teams": {
                                "away": {
                                    "team": {"name": "Seattle Mariners"},
                                    "score": 0,
                                },
                                "home": {
                                    "team": {"name": "Los Angeles Angels"},
                                    "score": 0,
                                },
                            },
                            "status": {"detailedState": "Scheduled"},
                            "gameDate": game_time,
                            "venue": {"name": "Angel Stadium"},
                        }
                    ]
                }
            ]
        }

        requests_mock.get(
            f"{MLB_API_BASE}/schedule/games/?sportId=1&date={today}&hydrate=linescore",
            json=games_response,
        )

        # Act
        games = fetch_mlb_games()

        # Assert
        assert len(games) == 1
        game = games[0]
        assert game["away_team"] == "Seattle Mariners"
        assert game["home_team"] == "Los Angeles Angels"
        assert game["away_score"] == 0
        assert game["home_score"] == 0
        assert "PM ET" in game["status"]
        assert "bases" not in game  # No bases for scheduled games
        assert "outs" not in game

    def test_fetch_mlb_games_final(self, requests_mock):
        """Test parsing a final MLB game"""
        # Arrange - Mock standings
        current_year = datetime.now().year
        requests_mock.get(
            f"{MLB_API_BASE}/standings?leagueId=103,104&season={current_year}",
            json={"records": []},
        )

        # Arrange - Mock final game
        today = datetime.now().strftime("%Y-%m-%d")
        games_response = {
            "dates": [
                {
                    "games": [
                        {
                            "teams": {
                                "away": {
                                    "team": {"name": "Chicago Cubs"},
                                    "score": 8,
                                },
                                "home": {
                                    "team": {"name": "St. Louis Cardinals"},
                                    "score": 4,
                                },
                            },
                            "status": {"detailedState": "Final"},
                            "linescore": {},
                            "venue": {"name": "Busch Stadium"},
                        }
                    ]
                }
            ]
        }

        requests_mock.get(
            f"{MLB_API_BASE}/schedule/games/?sportId=1&date={today}&hydrate=linescore",
            json=games_response,
        )

        # Act
        games = fetch_mlb_games()

        # Assert
        assert len(games) == 1
        game = games[0]
        assert game["status"] == "Final"
        assert "bases" not in game
        assert "outs" not in game

    def test_fetch_mlb_games_no_games_today(self, requests_mock):
        """Test handling when no games are scheduled"""
        # Arrange
        current_year = datetime.now().year
        requests_mock.get(
            f"{MLB_API_BASE}/standings?leagueId=103,104&season={current_year}",
            json={"records": []},
        )

        today = datetime.now().strftime("%Y-%m-%d")
        requests_mock.get(
            f"{MLB_API_BASE}/schedule/games/?sportId=1&date={today}&hydrate=linescore",
            json={"dates": []},
        )

        # Act
        games = fetch_mlb_games()

        # Assert
        assert games == []

    def test_fetch_mlb_games_api_failure(self, requests_mock):
        """Test that games API failure returns empty list"""
        # Arrange
        current_year = datetime.now().year
        requests_mock.get(
            f"{MLB_API_BASE}/standings?leagueId=103,104&season={current_year}",
            json={"records": []},
        )

        today = datetime.now().strftime("%Y-%m-%d")
        requests_mock.get(
            f"{MLB_API_BASE}/schedule/games/?sportId=1&date={today}&hydrate=linescore",
            status_code=500,
        )

        # Act
        games = fetch_mlb_games()

        # Assert
        assert games == []


@pytest.mark.unit
class TestNFLGames:
    """Tests for NFL games fetching"""

    def test_fetch_nfl_games_live_game(self, requests_mock):
        """Test parsing a live NFL game"""
        # Arrange
        mock_response = {
            "events": [
                {
                    "date": "2024-09-15T13:00:00Z",
                    "status": {
                        "type": {"description": "In Progress"},
                    },
                    "competitions": [
                        {
                            "competitors": [
                                {
                                    "homeAway": "home",
                                    "team": {"displayName": "Buffalo Bills"},
                                    "score": "21",
                                },
                                {
                                    "homeAway": "away",
                                    "team": {"displayName": "Kansas City Chiefs"},
                                    "score": "17",
                                },
                            ],
                            "status": {
                                "period": 3,
                                "displayClock": "8:42",
                            },
                        }
                    ],
                }
            ]
        }

        requests_mock.get(f"{NFL_API_BASE}/scoreboard", json=mock_response)

        # Act
        games = fetch_nfl_games()

        # Assert
        assert len(games) == 1
        game = games[0]
        assert game["away_team"] == "Kansas City Chiefs"
        assert game["home_team"] == "Buffalo Bills"
        assert game["away_score"] == 17
        assert game["home_score"] == 21
        assert game["status"] == "Q3 8:42"

    def test_fetch_nfl_games_scheduled(self, requests_mock):
        """Test parsing a scheduled NFL game"""
        # Arrange
        mock_response = {
            "events": [
                {
                    "date": "2024-09-15T20:15:00Z",
                    "status": {
                        "type": {"description": "Scheduled"},
                    },
                    "competitions": [
                        {
                            "competitors": [
                                {
                                    "homeAway": "home",
                                    "team": {"displayName": "Dallas Cowboys"},
                                    "score": "0",
                                },
                                {
                                    "homeAway": "away",
                                    "team": {"displayName": "Philadelphia Eagles"},
                                    "score": "0",
                                },
                            ],
                            "status": {},
                        }
                    ],
                }
            ]
        }

        requests_mock.get(f"{NFL_API_BASE}/scoreboard", json=mock_response)

        # Act
        games = fetch_nfl_games()

        # Assert
        assert len(games) == 1
        game = games[0]
        # Status gets converted to game time format (e.g., "8:15 PM ET")
        assert "PM ET" in game["status"] or "AM ET" in game["status"]

    def test_fetch_nfl_games_limits_to_six(self, requests_mock):
        """Test that NFL games are limited to 6"""
        # Arrange - Create 10 games
        events = []
        for i in range(10):
            events.append(
                {
                    "date": "2024-09-15T13:00:00Z",
                    "status": {"type": {"description": "Final"}},
                    "competitions": [
                        {
                            "competitors": [
                                {
                                    "homeAway": "home",
                                    "team": {"displayName": f"Home Team {i}"},
                                    "score": "10",
                                },
                                {
                                    "homeAway": "away",
                                    "team": {"displayName": f"Away Team {i}"},
                                    "score": "7",
                                },
                            ],
                            "status": {},
                        }
                    ],
                }
            )

        requests_mock.get(f"{NFL_API_BASE}/scoreboard", json={"events": events})

        # Act
        games = fetch_nfl_games()

        # Assert
        assert len(games) == 6

    def test_fetch_nfl_games_api_failure(self, requests_mock):
        """Test that NFL API failure returns empty list"""
        # Arrange
        requests_mock.get(f"{NFL_API_BASE}/scoreboard", status_code=500)

        # Act
        games = fetch_nfl_games()

        # Assert
        assert games == []

    def test_fetch_nfl_games_timeout(self, requests_mock):
        """Test that NFL API timeout returns empty list"""
        # Arrange
        requests_mock.get(f"{NFL_API_BASE}/scoreboard", exc=requests.exceptions.Timeout)

        # Act
        games = fetch_nfl_games()

        # Assert
        assert games == []

    def test_fetch_nfl_games_empty_response(self, requests_mock):
        """Test handling of empty NFL API response"""
        # Arrange
        requests_mock.get(f"{NFL_API_BASE}/scoreboard", json={"events": []})

        # Act
        games = fetch_nfl_games()

        # Assert
        assert games == []


@pytest.mark.unit
class TestCheckAllGamesFinal:
    """Tests for the check_all_games_final helper."""

    def test_all_games_final(self):
        games = [
            {"status": "Final"},
            {"status": "Final"},
            {"status": "Game Over"},
        ]
        assert check_all_games_final(games) is True

    def test_mixed_statuses(self):
        games = [
            {"status": "Final"},
            {"status": "Top 7th"},
            {"status": "7:05 PM ET"},
        ]
        assert check_all_games_final(games) is False

    def test_empty_games(self):
        assert check_all_games_final([]) is False

    def test_all_active(self):
        games = [
            {"status": "Bottom 3rd"},
            {"status": "Top 7th"},
        ]
        assert check_all_games_final(games) is False

    def test_postponed_counts_as_final(self):
        """Postponed games are in finalGameStatuses config."""
        games = [
            {"status": "Final"},
            {"status": "Postponed"},
        ]
        assert check_all_games_final(games) is True

    def test_one_scheduled_game_not_final(self):
        games = [
            {"status": "Final"},
            {"status": "Final"},
            {"status": "7:05 PM ET"},
        ]
        assert check_all_games_final(games) is False
