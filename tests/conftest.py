"""
Shared pytest fixtures for the test suite.

This file contains fixtures that are automatically available to all tests.
"""

from unittest.mock import Mock

import pytest
from flask import Flask


@pytest.fixture
def mock_mlb_api_response():
    """Mock response from MLB Stats API"""
    return {
        "dates": [
            {
                "games": [
                    {
                        "gamePk": 12345,
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
                        "status": {
                            "detailedState": "Final",
                        },
                        "linescore": {
                            "currentInning": 9,
                            "inningState": "End",
                            "outs": 3,
                        },
                        "venue": {"name": "Fenway Park"},
                    }
                ]
            }
        ]
    }


@pytest.fixture
def mock_nfl_api_response():
    """Mock response from ESPN NFL API"""
    return {
        "events": [
            {
                "name": "Kansas City Chiefs at Buffalo Bills",
                "shortName": "KC @ BUF",
                "competitions": [
                    {
                        "competitors": [
                            {
                                "team": {"displayName": "Buffalo Bills"},
                                "score": "21",
                                "homeAway": "home",
                            },
                            {
                                "team": {"displayName": "Kansas City Chiefs"},
                                "score": "17",
                                "homeAway": "away",
                            },
                        ],
                        "status": {
                            "type": {"description": "In Progress"},
                            "displayClock": "8:42",
                            "period": 3,
                        },
                    }
                ],
            }
        ]
    }


@pytest.fixture
def flask_app():
    """Create a Flask app for testing"""
    app = Flask(__name__)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def flask_client(flask_app):
    """Create a Flask test client"""
    return flask_app.test_client()


@pytest.fixture
def mock_requests_session():
    """Mock requests.Session for testing API calls"""
    session = Mock()
    session.get = Mock()
    return session
