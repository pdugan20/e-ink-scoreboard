# Sports Scores Plugin for InkyPi

Display live sports scores on your InkyPi e-ink display!

## Features

- **MLB Scores**: Real-time baseball game scores with inning information
- **NFL Scores**: Football game scores with quarter and clock information
- **Team Filtering**: Option to show only your favorite team's games
- **Auto-refresh**: Configurable refresh interval (5-60 minutes)
- **Clean Display**: Optimized layout for e-ink displays
- **Responsive Design**: Works with 800x400 and 1600x1200 displays

## Installation

### Option 1: Install in existing InkyPi setup

1. Copy the plugin files to your InkyPi installation:
   ```bash
   cp -r * /path/to/InkyPi/src/plugins/sports_scores/
   ```

2. Restart your InkyPi service
3. Navigate to your InkyPi web interface
4. Select "Sports Scores" from the plugin list

### Option 2: Clone and test standalone

1. Clone this repository:
   ```bash
   git clone <this-repo-url>
   cd sports-scores-plugin
   ```

2. Set up virtual environment and dependencies:
   ```bash
   # Create virtual environment (one time setup)
   python3 -m venv venv
   
   # Activate virtual environment (for pip commands)
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. Development workflow:
   ```bash
   # For running scripts, use explicit venv path (most reliable)
   ./venv/bin/python dev_server.py
   
   # For installing packages, activate venv first
   source venv/bin/activate
   pip install new-package
   
   # When done working
   deactivate  # Exit virtual environment (optional)
   ```

## Development & Testing

### Interactive Preview
Open `preview.html` in your browser for immediate visual feedback:
- Test different display sizes (800x400, 1600x1200)
- Load sample MLB/NFL data
- See live layout updates

### Development Server (Hot Reload + Live Data)
Run the dev server for rapid development:
```bash
# Hot reload server - auto-refreshes when you save CSS/HTML
./venv/bin/python dev_server.py
```

Features:
- **Hot reload**: Browser automatically refreshes when you save `static/styles.css` or `preview.html`
- **Live API data**: Click "Fetch Live Data" for real scores
- **Separated concerns**: CSS is in `static/styles.css`, HTML in `preview.html`

Then open http://localhost:5000 - you'll see a green "Hot reload active" indicator

### Configuration
Edit settings in the InkyPi web interface:
1. **Sports League**: Choose between MLB and NFL
2. **Favorite Team**: Filter scores for specific team (optional)
3. **Refresh Interval**: Set update frequency (5-60 minutes)

## API Sources
- MLB data from MLB Stats API (statsapi.mlb.com)
- NFL data from ESPN API

## File Structure
```
sports-scores-plugin/
├── sports_scores.py    # Main plugin class
├── plugin-info.json    # Plugin metadata
├── settings.html       # Configuration UI
├── preview.html        # Development preview
├── dev_server.py       # Development server
├── requirements.txt    # Dependencies
└── README.md          # This file
```

## Future Enhancements
- NBA scores
- NHL scores  
- Team standings
- Game predictions
- Player statistics
- Multiple team favorites