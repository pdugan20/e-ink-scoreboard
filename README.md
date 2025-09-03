# Sports Scores E-ink Display

Display live sports scores on your e-ink display with professional quality and real-time updates!

## Features

- **Live MLB Scores**: Real-time baseball game scores with inning information
- **Professional Quality**: 2x DPI rendering for crisp text and team logos
- **Clean Layout**: Optimized 800x480 display showing up to 15 games in a 3x5 grid
- **Auto-refresh**: Configurable refresh interval (5 minutes to 2+ hours)
- **Mac Testing**: Full development environment with live preview
- **Raspberry Pi Ready**: Complete deployment guide with systemd services

## Quick Start

### Mac Development/Testing

1. **Clone and setup**:
   ```bash
   git clone [YOUR_REPO_URL]
   cd sports-scores-plugin
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Test the display**:
   ```bash
   # Start web server
   python dev_server.py --port 5001
   
   # Take screenshot (in another terminal)
   source venv/bin/activate
   python eink_display.py --once
   
   # View result: test_display_output.png
   ```

3. **View in browser**: http://localhost:5001/display

### Raspberry Pi Deployment

See **[RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md)** for complete installation instructions.

## Configuration

Edit `eink_config.json` to customize:

```json
{
  "web_server_url": "http://localhost:5001/display",
  "display_width": 800,
  "display_height": 480,
  "screenshot_scale": 2,
  "refresh_interval": 300,
  "max_retries": 3,
  "retry_delay": 5
}
```

**Refresh Intervals:**
- **300 seconds (5 minutes)** - Default, good for active game times
- **900 seconds (15 minutes)** - Balanced for general use  
- **1800 seconds (30 minutes)** - Conservative, preserves display life
- **3600+ seconds (1+ hours)** - Minimal updates for overnight/off-season

## Technical Details

### Screenshot Quality
- **Playwright rendering**: Precise 800x480 viewport with 2x DPI
- **High-res capture**: 1600x960 screenshot for crisp text/logos
- **Smart downsampling**: LANCZOS filtering to 800x480 final image
- **Fallback support**: Chrome/Chromium headless if Playwright unavailable

### Data Sources
- **Live MLB data**: ESPN API with real-time scores and game status
- **Team logos**: High-resolution SVG assets
- **Game information**: Scores, innings, times, venues, game status

### Display Layout
- **Header**: League logo, current date, timestamp
- **Games grid**: 3x4 layout showing 12 current games
- **Game cards**: Team logos, scores, game status, venue/time info
- **Status indicators**: Final, live innings, scheduled start times

## Files Structure

- `eink_display.py` - Main display controller (Mac + Pi compatible)
- `dev_server.py` - Development web server with hot reload
- `display.html` - Clean display endpoint (no dev UI)
- `preview.html` - Development preview with controls
- `eink_config.json` - Display configuration
- `RASPBERRY_PI_SETUP.md` - Complete Pi deployment guide
- `static/` - CSS, JavaScript, fonts, logos

## Commands

```bash
# Single update
python eink_display.py --once

# Continuous updates (default 5min interval)  
python eink_display.py

# Custom interval (10 minutes)
python eink_display.py --interval 600

# Custom config file
python eink_display.py --config my_config.json

# Custom server URL
python eink_display.py --url http://localhost:5002/display
```

## Development

- **Preview**: http://localhost:5001/ (dev controls)
- **Clean display**: http://localhost:5001/display (screenshot target)
- **Hot reload**: Auto-refresh on file changes
- **Live data**: Fetch button to get current MLB scores

## Requirements

- Python 3.8+
- Playwright (for high-quality screenshots)
- Flask (web server)
- Pillow (image processing)
- Inky library (Raspberry Pi only)

## License

MIT License - see LICENSE file for details