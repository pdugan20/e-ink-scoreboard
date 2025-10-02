# API Examples and Testing

This document provides practical examples for testing and using the E-Ink Sports Scores API endpoints.

## Testing the API

### Prerequisites

Make sure the development server is running:

```bash
cd ~/sports-scores-plugin  # or your project directory
source venv/bin/activate

python src/dev_server.py --port 5001
```

## Example API Calls

### 1. MLB Scores

#### Basic Request

```bash
curl "http://localhost:5001/api/scores/MLB"
```

#### Sample Response - Live Game

```json
[
  {
    "away_team": "Seattle Mariners",
    "home_team": "Los Angeles Angels",
    "away_score": 5,
    "home_score": 3,
    "away_record": "75-72",
    "home_record": "63-84",
    "status": "Top 8th",
    "venue": "Angel Stadium",
    "bases": {
      "first": true,
      "second": false,
      "third": true
    },
    "outs": 1
  },
  {
    "away_team": "New York Yankees",
    "home_team": "Tampa Bay Rays",
    "away_score": 0,
    "home_score": 0,
    "away_record": "82-65",
    "home_record": "70-77",
    "status": "7:10 PM ET",
    "venue": "Tropicana Field"
  }
]
```

#### Sample Response - Final Game

```json
[
  {
    "away_team": "Boston Red Sox",
    "home_team": "Baltimore Orioles",
    "away_score": 8,
    "home_score": 4,
    "away_record": "78-69",
    "home_record": "89-58",
    "status": "Final",
    "venue": "Oriole Park at Camden Yards"
  }
]
```

### 2. NFL Scores

#### Basic Request

```bash
curl "http://localhost:5001/api/scores/NFL"
```

#### Sample Response

```json
[
  {
    "away_team": "Kansas City Chiefs",
    "home_team": "Buffalo Bills",
    "away_score": 21,
    "home_score": 17,
    "status": "Q4 3:42"
  },
  {
    "away_team": "Dallas Cowboys",
    "home_team": "Philadelphia Eagles",
    "away_score": 0,
    "home_score": 0,
    "status": "1:00 PM ET"
  }
]
```

### 3. Screensaver API

#### Basic Request

```bash
curl "http://localhost:5001/api/screensaver/MLB"
```

#### Sample Response - Success

```json
{
  "title": "Mariners Clinch Wild Card Berth with 7-3 Victory",
  "description": "The Seattle Mariners secured their playoff spot with a dominant performance against the Angels, highlighted by Julio Rodríguez's two home runs and stellar pitching from Logan Gilbert...",
  "published": "September 8, 2025",
  "image_url": "https://www.seattletimes.com/wp-content/uploads/2025/09/mariners-celebration.jpg?d=800x480",
  "link": "https://www.seattletimes.com/sports/mariners/mariners-clinch-wild-card-berth/",
  "team": "Seattle Mariners",
  "type": "screensaver"
}
```

#### Sample Response - No Feed Configured

```json
{
  "error": "No RSS feed configured for favorite teams",
  "title": "Unable to load news",
  "description": "News content is temporarily unavailable.",
  "published": "September 8, 2025",
  "image_url": null,
  "type": "screensaver"
}
```

### 4. Display Endpoints

#### Standard Display

```bash
curl "http://localhost:5001/display"
```

Returns HTML optimized for 800x480 e-ink display.

#### Test Data Display

```bash
curl "http://localhost:5001/display?test=true"
```

#### Screensaver Mode

```bash
curl "http://localhost:5001/display?screensaver=true"
```

## Testing with Different Scenarios

### 1. Test No Games Today

When there are no MLB games scheduled, the API automatically falls back to yesterday's completed games (limited to 6).

### 2. Test Live Game Status

The status field adapts to different game states:

**Scheduled Games:**

- `"7:10 PM ET"` - Start time in Eastern Time
- `"1:05 PM ET"` - Afternoon games

**Live Games:**

- `"Top 1st"` - Top of first inning
- `"Bot 9th"` - Bottom of ninth inning
- `"In Progress"` - Fallback when inning data unavailable

**Completed Games:**

- `"Final"` - Regular game completion

### 3. Test Base Runners and Outs

Live baseball games include additional fields:

```json
{
  "bases": {
    "first": true, // Runner on first base
    "second": false, // No runner on second
    "third": true // Runner on third base
  },
  "outs": 2 // Current number of outs (0, 1, or 2)
}
```

## Error Testing

### 1. Invalid League

```bash
curl "http://localhost:5001/api/scores/INVALID"
# Returns: {"error": "Invalid league"}
```

### 2. Server Unavailable

When external APIs (MLB Stats API, ESPN) are unavailable:

```bash
# Typically returns empty array [] or error message
curl "http://localhost:5001/api/scores/MLB"
```

### 3. Network Issues

The API includes timeout handling (10 seconds) and graceful error responses.

## Browser Testing

### 1. Live Display Preview

Visit: `http://localhost:5001/display`

### 2. Test Data Preview

Visit: `http://localhost:5001/display?test=true`

### 3. Screensaver Preview

Visit: `http://localhost:5001/display?screensaver=true`

### 4. Development Interface

Visit: `http://localhost:5001/` (includes hot reload and controls)

## E-Ink Display Testing

### 1. Screenshot Test

```bash
source venv/bin/activate
python src/eink_display.py --once --url "http://localhost:5001/display"
```

### 2. Force Screensaver Test

```bash
python src/eink_display.py --once --url "http://localhost:5001/display?screensaver=true"
```

### 3. Test Data Display

```bash
python src/eink_display.py --once --url "http://localhost:5001/display?test=true"
```

## Useful Testing Commands

### Monitor API Responses

```bash
# Watch MLB API for changes
watch -n 30 'curl -s "http://localhost:5001/api/scores/MLB" | jq'

# Monitor screensaver API
curl -s "http://localhost:5001/api/screensaver/MLB" | jq
```

### Check Server Logs

```bash
# If running as development server, logs appear in terminal
# For systemd service:
sudo journalctl -u sports-server.service --follow
```

### Validate JSON Responses

```bash
# Pretty print JSON responses
curl -s "http://localhost:5001/api/scores/MLB" | python -m json.tool

# Or use jq if available
curl -s "http://localhost:5001/api/scores/MLB" | jq '.'
```

## Performance Testing

### Response Times

Typical response times:

- MLB Scores: 1-3 seconds (external API call)
- NFL Scores: 1-3 seconds (external API call)
- Screensaver: 2-5 seconds (RSS parsing)
- Display HTML: <100ms (local file)

### Load Testing

```bash
# Simple load test - 10 concurrent requests
for i in {1..10}; do
  curl "http://localhost:5001/api/scores/MLB" &
done
wait
```

## Troubleshooting API Issues

### Common Issues

1. **Empty Response `[]`**
   - No games scheduled today
   - External API unavailable
   - Network connectivity issues

2. **JSON Parse Errors**
   - External API returned non-JSON
   - Network timeout occurred
   - Check server logs for details

3. **Screensaver Errors**
   - No favorite teams configured
   - RSS feed unavailable
   - Invalid RSS feed format

### Debug Steps

1. **Test External APIs Directly:**

```bash
# Test MLB API directly
curl "https://statsapi.mlb.com/api/v1/schedule/games/?sportId=1&date=$(date +%Y-%m-%d)"

# Test ESPN NFL API
curl "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
```

2. **Check Configuration:**

```bash
# Verify favorite teams configuration
cat src/static/js/config.js

# Check RSS feed config (if it exists)
ls -la config/team-rss-feeds.json
```

3. **Monitor Server Logs:**

```bash
# Development server shows logs in terminal
# Production: check systemd logs
sudo journalctl -u sports-server.service --since "1 hour ago"
```
