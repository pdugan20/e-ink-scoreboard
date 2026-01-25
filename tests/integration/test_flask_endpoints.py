"""
Integration tests for Flask API endpoints.

Tests the full request/response cycle through the Flask app.
"""

import os
import sys
from datetime import datetime

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))

from dev_server import app  # noqa: E402


@pytest.fixture
def client():
    """Create a Flask test client"""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.mark.integration
class TestMLBScoresEndpoint:
    """Integration tests for /api/scores/MLB endpoint"""

    def test_mlb_scores_success(self, client, requests_mock):
        """Test successful MLB scores fetch"""
        # Arrange
        current_year = datetime.now().year
        requests_mock.get(
            f"https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season={current_year}",
            json={"records": []},
        )

        today = datetime.now().strftime("%Y-%m-%d")
        requests_mock.get(
            f"https://statsapi.mlb.com/api/v1/schedule/games/?sportId=1&date={today}&hydrate=linescore",
            json={
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
                                "status": {"detailedState": "Final"},
                                "linescore": {},
                                "venue": {"name": "Fenway Park"},
                            }
                        ]
                    }
                ]
            },
        )

        # Act
        response = client.get("/api/scores/MLB")

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["away_team"] == "New York Yankees"
        assert data[0]["home_team"] == "Boston Red Sox"

    def test_mlb_scores_api_error(self, client, requests_mock):
        """Test MLB scores when API fails"""
        # Arrange
        current_year = datetime.now().year
        requests_mock.get(
            f"https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season={current_year}",
            status_code=500,
        )

        # Act
        response = client.get("/api/scores/MLB")

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 0  # Returns empty list on error


@pytest.mark.integration
class TestNFLScoresEndpoint:
    """Integration tests for /api/scores/NFL endpoint"""

    def test_nfl_scores_success(self, client, requests_mock):
        """Test successful NFL scores fetch"""
        # Arrange
        requests_mock.get(
            "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
            json={
                "events": [
                    {
                        "date": "2024-09-15T13:00:00Z",
                        "status": {"type": {"description": "Final"}},
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
                                "status": {},
                            }
                        ],
                    }
                ]
            },
        )

        # Act
        response = client.get("/api/scores/NFL")

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["home_team"] == "Buffalo Bills"
        assert data[0]["away_team"] == "Kansas City Chiefs"

    def test_nfl_scores_api_error(self, client, requests_mock):
        """Test NFL scores when API fails"""
        # Arrange
        requests_mock.get(
            "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
            status_code=503,
        )

        # Act
        response = client.get("/api/scores/NFL")

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 0  # Returns empty list on error


@pytest.mark.integration
class TestInvalidLeagueEndpoint:
    """Integration tests for invalid league"""

    def test_invalid_league(self, client):
        """Test request for invalid league"""
        # Act
        response = client.get("/api/scores/NBA")

        # Assert
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert data["error"] == "Invalid league"


@pytest.mark.integration
class TestScreensaverEndpoint:
    """Integration tests for /api/screensaver/<league> endpoint"""

    def test_screensaver_no_favorite_teams(self, client):
        """Test screensaver when no favorite teams configured"""
        # Act
        response = client.get("/api/screensaver/mlb")

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        # Should return empty dict when no favorites
        assert isinstance(data, dict)

    def test_screensaver_invalid_league(self, client):
        """Test screensaver with league not in config"""
        # Act
        response = client.get("/api/screensaver/nba")

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        # Should return empty dict for unconfigured league
        assert isinstance(data, dict)


@pytest.mark.integration
class TestRootEndpoint:
    """Integration tests for / endpoint"""

    def test_root_endpoint_returns_html(self, client):
        """Test that root endpoint returns HTML"""
        # Act
        response = client.get("/")

        # Assert
        assert response.status_code == 200
        assert response.content_type.startswith("text/html")


@pytest.mark.integration
class TestDisplayEndpoint:
    """Integration tests for /display endpoint"""

    def test_display_endpoint_returns_html(self, client):
        """Test that display endpoint returns HTML"""
        # Act
        response = client.get("/display")

        # Assert
        assert response.status_code == 200
        assert response.content_type.startswith("text/html")
