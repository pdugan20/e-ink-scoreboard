"""
Screensaver service for fetching and processing team news articles.
Handles RSS feed parsing with pluggable parsers for different sources.
"""

import json
import os
import random
import re
from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin
import feedparser


class ScreensaverService:
    """Service for managing team-based screensaver content."""
    
    def __init__(self, config_path=None):
        """Initialize the screensaver service with RSS feed configuration."""
        if config_path is None:
            # Default to the config file in the same directory structure
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(os.path.dirname(current_dir), 'config', 'team-rss-feeds.json')
        
        self.config_path = config_path
        self.rss_feeds = self._load_rss_config()
        self.parsers = {}
        self._register_parsers()
    
    def _load_rss_config(self):
        """Load RSS feed configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load RSS config from {self.config_path}: {e}")
            return {}
    
    def _register_parsers(self):
        """Register RSS parsers for different feed sources."""
        # For now, we'll use a simple approach since we only have the proxy RSS
        # Future parsers can be added here as we expand to other sources
        pass
    
    def get_team_rss_url(self, team_name, league='mlb'):
        """Get RSS URL for a specific team."""
        league_feeds = self.rss_feeds.get(league, {})
        return league_feeds.get(team_name)
    
    def get_favorite_team_rss_url(self, favorite_teams, league='mlb'):
        """Get RSS URL for the first favorite team that has a configured feed."""
        if not favorite_teams:
            return None, None
            
        # Handle both string and array formats for favorite teams
        if isinstance(favorite_teams, str):
            favorite_teams = [favorite_teams]
        elif not isinstance(favorite_teams, list):
            return None, None
        
        # Try to find RSS feed for the first favorite team
        for team in favorite_teams:
            rss_url = self.get_team_rss_url(team, league)
            if rss_url:
                return rss_url, team
        
        return None, None
    
    def fetch_article(self, team_name, league='mlb'):
        """Fetch a random article for the specified team."""
        rss_url = self.get_team_rss_url(team_name, league)
        
        if not rss_url:
            return self._create_error_response(f"No RSS feed configured for {team_name}")
        
        return self._fetch_article_from_rss(rss_url, team_name)
    
    def fetch_article_for_favorites(self, favorite_teams, league='mlb'):
        """Fetch article for the first available favorite team."""
        rss_url, team_name = self.get_favorite_team_rss_url(favorite_teams, league)
        
        if not rss_url:
            return self._create_error_response("No RSS feed configured for favorite teams")
        
        return self._fetch_article_from_rss(rss_url, team_name)
    
    def _fetch_article_from_rss(self, rss_url, team_name):
        """Fetch and parse article from RSS feed."""
        try:
            # Parse the RSS feed (proxy handles all the complexity)
            feed = feedparser.parse(rss_url)
            
            if not feed.entries:
                return self._create_error_response(f"No articles found for {team_name}")
            
            # Get the last 10 articles (or fewer if there aren't 10)
            recent_articles = feed.entries[:10]
            
            # Choose one article at random
            selected_article = random.choice(recent_articles)
            
            # Process the article data
            return self._process_article(selected_article, team_name)
            
        except Exception as e:
            return self._create_error_response(f"Error fetching article for {team_name}: {str(e)}")
    
    def _process_article(self, article, team_name):
        """Process and format article data."""
        # Extract article information
        title = article.get('title', f'{team_name} News')
        description = article.get('summary', '')
        published = article.get('published', '')
        
        # Parse and format the published date
        published_date = self._format_published_date(published)
        
        # Extract image URL
        image_url = self._extract_image_url(article)
        
        # Clean up the description and title
        description = self._clean_html_content(description, max_length=200)
        title = self._clean_html_content(title)
        
        # Format image URL for display
        if image_url:
            image_url = self._format_image_url(image_url)
        
        return {
            'title': title,
            'description': description,
            'published': published_date,
            'image_url': image_url,
            'link': article.get('link', ''),
            'team': team_name,
            'type': 'screensaver'
        }
    
    def _format_published_date(self, published):
        """Format the published date for display."""
        if not published:
            return datetime.now().strftime('%B %d, %Y')
            
        try:
            published_dt = parsedate_to_datetime(published)
            return published_dt.strftime('%B %d, %Y')
        except Exception as e:
            print(f"Could not parse date: {published}, error: {e}")
            return published
    
    def _extract_image_url(self, article):
        """Extract image URL from article content."""
        
        image_url = None
        
        # Look for enclosures first (this RSS format uses enclosure tags)
        if hasattr(article, 'enclosures') and article.enclosures:
            for enclosure in article.enclosures:
                if enclosure.get('type', '').startswith('image/'):
                    image_url = enclosure.get('href') or enclosure.get('url')
                    break
        
        # Look for media content as backup
        if not image_url and hasattr(article, 'media_content'):
            for media in article.media_content:
                if media.get('type', '').startswith('image/') or media.get('medium') == 'image':
                    image_url = media.get('url')
                    break
        
        # Look for images in the content if no media found
        if not image_url and hasattr(article, 'content'):
            content = article.content[0].get('value', '') if article.content else ''
            img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>', content)
            if img_match:
                image_url = img_match.group(1)
        
        # If still no image, look in summary
        if not image_url and hasattr(article, 'summary'):
            summary = article.get('summary', '')
            img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>', summary)
            if img_match:
                image_url = img_match.group(1)
        
        return image_url
    
    def _format_image_url(self, image_url):
        """Format image URL for proper display dimensions."""
        
        # Ensure image URL is absolute
        if image_url and not image_url.startswith('http'):
            image_url = urljoin('https://www.seattletimes.com', image_url)
        
        # Modify Seattle Times image URLs to request 800x480 size
        if image_url and 'seattletimes.com' in image_url:
            target_dimensions = "800x480"  # Full screen dimensions
            
            if '?d=' in image_url:
                image_url = re.sub(r'\?d=\d+x\d+', f'?d={target_dimensions}', image_url)
            else:
                separator = '&' if '?' in image_url else '?'
                image_url = f"{image_url}{separator}d={target_dimensions}"
        
        return image_url
    
    def _clean_html_content(self, content, max_length=None):
        """Clean HTML tags from content and optionally truncate."""
        
        if not content:
            return ''
            
        # Remove HTML tags
        content = re.sub(r'<[^>]+>', '', content).strip()
        
        # Truncate if too long
        if max_length and len(content) > max_length:
            content = content[:max_length] + '...'
        
        return content
    
    def _create_error_response(self, error_message):
        """Create a standardized error response."""
        return {
            'error': error_message,
            'title': 'Unable to load news',
            'description': 'News content is temporarily unavailable.',
            'published': datetime.now().strftime('%B %d, %Y'),
            'image_url': None,
            'type': 'screensaver'
        }