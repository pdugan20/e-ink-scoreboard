"""
Unit tests for ScreensaverService.

Tests RSS feed URL resolution, image orientation filtering,
image URL formatting, and article processing.
"""

import json

from unittest.mock import MagicMock

import pytest

from src.services.screensaver_service import ScreensaverService


def _create_config_file(tmp_path, config=None):
    """Helper to create a temp RSS config JSON file."""
    if config is None:
        config = {
            "mlb": {
                "Seattle Mariners": {
                    "news": "https://example.com/news-feed",
                    "photos": "https://example.com/photos-feed",
                }
            }
        }
    config_path = tmp_path / "team-rss-feeds.json"
    config_path.write_text(json.dumps(config))
    return str(config_path)


@pytest.mark.unit
class TestGetTeamRssUrl:
    """Tests for get_team_rss_url with nested dict format."""

    def test_returns_news_url_for_news_feed_type(self, tmp_path):
        """Test that news feed_type returns the news URL."""
        # Arrange
        config_path = _create_config_file(tmp_path)
        service = ScreensaverService(config_path=config_path)

        # Act
        result = service.get_team_rss_url("Seattle Mariners", feed_type="news")

        # Assert
        assert result == "https://example.com/news-feed"

    def test_returns_photos_url_for_photos_feed_type(self, tmp_path):
        """Test that photos feed_type returns the photos URL."""
        # Arrange
        config_path = _create_config_file(tmp_path)
        service = ScreensaverService(config_path=config_path)

        # Act
        result = service.get_team_rss_url("Seattle Mariners", feed_type="photos")

        # Assert
        assert result == "https://example.com/photos-feed"

    def test_returns_none_for_unknown_team(self, tmp_path):
        """Test that an unknown team returns None."""
        # Arrange
        config_path = _create_config_file(tmp_path)
        service = ScreensaverService(config_path=config_path)

        # Act
        result = service.get_team_rss_url("Boston Red Sox", feed_type="news")

        # Assert
        assert result is None

    def test_returns_none_for_missing_feed_type(self, tmp_path):
        """Test that a team with only news configured returns None for photos."""
        # Arrange
        config = {
            "mlb": {
                "Seattle Mariners": {
                    "news": "https://example.com/news-feed",
                }
            }
        }
        config_path = _create_config_file(tmp_path, config)
        service = ScreensaverService(config_path=config_path)

        # Act
        result = service.get_team_rss_url("Seattle Mariners", feed_type="photos")

        # Assert
        assert result is None


@pytest.mark.unit
class TestIsLandscapeImage:
    """Tests for _is_landscape_image orientation filtering."""

    def test_returns_true_for_landscape_image(self, tmp_path):
        """Test that a landscape image (width > height) returns True."""
        # Arrange
        config_path = _create_config_file(tmp_path)
        service = ScreensaverService(config_path=config_path)
        article = MagicMock()
        article.media_content = [{"width": "512", "height": "341"}]

        # Act
        result = service._is_landscape_image(article)

        # Assert
        assert result is True

    def test_returns_false_for_portrait_image(self, tmp_path):
        """Test that a portrait image (height > width) returns False."""
        # Arrange
        config_path = _create_config_file(tmp_path)
        service = ScreensaverService(config_path=config_path)
        article = MagicMock()
        article.media_content = [{"width": "409", "height": "512"}]

        # Act
        result = service._is_landscape_image(article)

        # Assert
        assert result is False

    def test_returns_true_when_no_media_content(self, tmp_path):
        """Test that articles without media_content are not filtered out."""
        # Arrange
        config_path = _create_config_file(tmp_path)
        service = ScreensaverService(config_path=config_path)
        article = MagicMock(spec=[])  # No attributes at all

        # Act
        result = service._is_landscape_image(article)

        # Assert
        assert result is True

    def test_returns_true_when_dimensions_missing(self, tmp_path):
        """Test that articles with media_content but no dimensions are not filtered."""
        # Arrange
        config_path = _create_config_file(tmp_path)
        service = ScreensaverService(config_path=config_path)
        article = MagicMock()
        article.media_content = [{"url": "https://example.com/image.jpg"}]

        # Act
        result = service._is_landscape_image(article)

        # Assert
        assert result is True


@pytest.mark.unit
class TestFormatImageUrl:
    """Tests for _format_image_url URL formatting logic."""

    def test_seattle_times_url_gets_dimensions_appended(self, tmp_path):
        """Test that Seattle Times URLs get ?d=800x480 appended."""
        # Arrange
        config_path = _create_config_file(tmp_path)
        service = ScreensaverService(config_path=config_path)
        url = "https://www.seattletimes.com/wp-content/uploads/image.jpg"

        # Act
        result = service._format_image_url(url)

        # Assert
        assert (
            result
            == "https://www.seattletimes.com/wp-content/uploads/image.jpg?d=800x480"
        )

    def test_non_seattle_times_url_passes_through(self, tmp_path):
        """Test that non-Seattle Times URLs are returned unchanged."""
        # Arrange
        config_path = _create_config_file(tmp_path)
        service = ScreensaverService(config_path=config_path)
        url = "https://cdn.espn.com/photos/image.jpg"

        # Act
        result = service._format_image_url(url)

        # Assert
        assert result == "https://cdn.espn.com/photos/image.jpg"

    def test_ap_photos_url_passes_through(self, tmp_path):
        """Test that AP Photos URLs pass through unchanged."""
        # Arrange
        config_path = _create_config_file(tmp_path)
        service = ScreensaverService(config_path=config_path)
        url = "https://mapi.associatedpress.com/v1/items/photo123/renditions/original"

        # Act
        result = service._format_image_url(url)

        # Assert
        assert (
            result
            == "https://mapi.associatedpress.com/v1/items/photo123/renditions/original"
        )


@pytest.mark.unit
class TestProcessArticle:
    """Tests for _process_article article formatting."""

    def _make_article(self):
        """Create a mock feedparser entry dict with standard fields."""
        return {
            "title": "Mariners Win Big",
            "summary": "The Mariners defeated the Astros 5-2.",
            "published": "Mon, 01 Apr 2026 12:00:00 GMT",
            "link": "https://example.com/article/1",
        }

    def test_adds_feed_source_key(self, tmp_path):
        """Test that feed_source key is added to the result."""
        # Arrange
        config_path = _create_config_file(tmp_path)
        service = ScreensaverService(config_path=config_path)
        article = self._make_article()

        # Act
        result = service._process_article(article, "Seattle Mariners", feed_type="news")

        # Assert
        assert "feed_source" in result

    def test_news_feed_source_for_news_articles(self, tmp_path):
        """Test that news articles get feed_source='news'."""
        # Arrange
        config_path = _create_config_file(tmp_path)
        service = ScreensaverService(config_path=config_path)
        article = self._make_article()

        # Act
        result = service._process_article(article, "Seattle Mariners", feed_type="news")

        # Assert
        assert result["feed_source"] == "news"

    def test_photos_feed_source_for_photo_articles(self, tmp_path):
        """Test that photo articles get feed_source='photos'."""
        # Arrange
        config_path = _create_config_file(tmp_path)
        service = ScreensaverService(config_path=config_path)
        article = self._make_article()

        # Act
        result = service._process_article(
            article, "Seattle Mariners", feed_type="photos"
        )

        # Assert
        assert result["feed_source"] == "photos"
