#!/bin/bash
# Interactive configuration for Sports Scores E-ink Display

set -e

# Change to project root directory (go up from scripts/ to project root)
cd "$(dirname "$0")/.."

echo "E-Ink Scoreboard Configuration"
echo "====================================="
echo ""

# Function to update JavaScript config  
update_js_config() {
    local file="$1"
    local key="$2" 
    local value="$3"
    
    # Use Python to safely update JavaScript config with proper escaping
    python3 -c """
import re
import sys

file_path = sys.argv[1]
key = sys.argv[2] 
value = sys.argv[3]

with open(file_path, 'r') as f:
    content = f.read()

# Update the specific export line safely
pattern = r'export const ' + re.escape(key) + r' = .*?;'
replacement = 'export const ' + key + ' = ' + value + ';'
content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open(file_path, 'w') as f:
    f.write(content)
""" "$file" "$key" "$value"
}

# Function to update JSON config
update_json_config() {
    local key="$1"
    local value="$2"
    
    python3 -c "
import json
with open('src/eink_config.json', 'r') as f:
    config = json.load(f)
config['$key'] = '$value'
with open('src/eink_config.json', 'w') as f:
    json.dump(config, f, indent=2)
"
}

echo "⚾️ Choose your favorite MLB team (will appear first when playing):"
echo ""
echo "American League:"
echo " 1) None                          9) Mariners"
echo " 2) Angels                       10) Orioles"
echo " 3) Astros                       11) Rangers"
echo " 4) Athletics                    12) Red Sox"
echo " 5) Blue Jays                    13) Royals"
echo " 6) Guardians                    14) Rays"
echo " 7) White Sox                    15) Tigers"
echo " 8) Twins                        16) Yankees"
echo ""
echo "National League:"
echo "17) D-backs                      25) Marlins"
echo "18) Braves                       26) Mets"
echo "19) Cubs                         27) Phillies"
echo "20) Reds                         28) Pirates"
echo "21) Rockies                      29) Cardinals"
echo "22) Dodgers                      30) Nationals"
echo "23) Giants"
echo "24) Brewers"
echo ""

read -p "Enter choice (1-30): " team_choice

# Map choice to team name (use the short names from the config)
case $team_choice in
    1) favorite_team="null" ;;
    2) favorite_team="'Angels'" ;;
    3) favorite_team="'Astros'" ;;
    4) favorite_team="'Athletics'" ;;
    5) favorite_team="'Blue Jays'" ;;
    6) favorite_team="'Guardians'" ;;
    7) favorite_team="'White Sox'" ;;
    8) favorite_team="'Twins'" ;;
    9) favorite_team="'Mariners'" ;;
    10) favorite_team="'Orioles'" ;;
    11) favorite_team="'Rangers'" ;;
    12) favorite_team="'Red Sox'" ;;
    13) favorite_team="'Royals'" ;;
    14) favorite_team="'Rays'" ;;
    15) favorite_team="'Tigers'" ;;
    16) favorite_team="'Yankees'" ;;
    17) favorite_team="'D-backs'" ;;
    18) favorite_team="'Braves'" ;;
    19) favorite_team="'Cubs'" ;;
    20) favorite_team="'Reds'" ;;
    21) favorite_team="'Rockies'" ;;
    22) favorite_team="'Dodgers'" ;;
    23) favorite_team="'Giants'" ;;
    24) favorite_team="'Brewers'" ;;
    25) favorite_team="'Marlins'" ;;
    26) favorite_team="'Mets'" ;;
    27) favorite_team="'Phillies'" ;;
    28) favorite_team="'Pirates'" ;;
    29) favorite_team="'Cardinals'" ;;
    30) favorite_team="'Nationals'" ;;
    *) echo "Invalid choice, skipping favorite team"; favorite_team="null" ;;
esac

if [ "$favorite_team" != "null" ]; then
    echo "✅ Set favorite team: $favorite_team"
    update_js_config "src/static/js/config.js" "favoriteTeams" "{ mlb: $favorite_team, nfl: null, cfb: null }"
else
    echo "✅ No favorite team selected"
fi

echo ""
echo "🌍 Choose your timezone:"
echo ""
echo " 1) US/Eastern (New York)        5) US/Mountain (Denver)"
echo " 2) US/Central (Chicago)         6) US/Pacific (Los Angeles)"  
echo " 3) US/Arizona (Phoenix)         7) Canada/Eastern (Toronto)"
echo " 4) US/Hawaii (Honolulu)         8) Other (enter manually)"
echo ""

read -p "Enter choice (1-8): " tz_choice

case $tz_choice in
    1) timezone="TIMEZONES.EASTERN"; timezone_display="US/Eastern" ;;
    2) timezone="TIMEZONES.CENTRAL"; timezone_display="US/Central" ;;
    3) timezone="TIMEZONES.ARIZONA"; timezone_display="US/Arizona" ;;
    4) timezone="TIMEZONES.HAWAII"; timezone_display="US/Hawaii" ;;
    5) timezone="TIMEZONES.MOUNTAIN"; timezone_display="US/Mountain" ;;
    6) timezone="TIMEZONES.PACIFIC"; timezone_display="US/Pacific" ;;
    7) timezone="'America/Toronto'"; timezone_display="Canada/Eastern" ;;
    8) 
        echo ""
        read -p "Enter timezone (e.g., Europe/London): " custom_tz
        timezone="'$custom_tz'"
        timezone_display="$custom_tz"
        ;;
    *) echo "Invalid choice, using US/Eastern"; timezone="TIMEZONES.EASTERN"; timezone_display="US/Eastern" ;;
esac

echo "✅ Set timezone: $timezone_display"
update_js_config "src/static/js/config.js" "displayTimezone" "$timezone"

echo ""
echo "🕒 Choose refresh interval:"
echo ""
echo " 1) 120 seconds - Live action"
echo " 2) 300 seconds - Semi-live updates" 
echo " 3) 900 seconds - General use"
echo ""

read -p "Enter choice (1-5): " interval_choice

case $interval_choice in
    1) interval=120 ;;
    2) interval=300 ;;
    3) interval=900 ;;
    *) echo "Invalid choice, using 2 minutes"; interval=120 ;;
esac

echo "✅ Set refresh interval: $interval seconds"
update_json_config "refresh_interval" "$interval"

echo ""
echo "🎨 Choose display theme:"
echo ""
echo " 1) Default - Clean with colorful team logos"
echo " 2) Team Colors - Dynamic backgrounds with both team's colors"
echo " 3) MLB Scoreboard - Classic scoreboard appearance"
echo ""

read -p "Enter choice (1-3): " theme_choice

case $theme_choice in
    1) theme="THEMES.DEFAULT"; theme_display="Default" ;;
    2) theme="THEMES.TEAM_COLORS"; theme_display="Team Colors" ;;
    3) theme="THEMES.MLB_SCOREBOARD"; theme_display="MLB Scoreboard" ;;
    *) echo "Invalid choice, using default"; theme="THEMES.DEFAULT"; theme_display="Default" ;;
esac

echo "✅ Set theme: $theme_display"
update_js_config "src/static/js/config.js" "currentTheme" "$theme"

echo ""
echo "🎉 Configuration complete!"
echo ""
echo "Your settings have been applied to:"
echo "- src/static/js/config.js (theme, timezone, favorite team)"
echo "- src/eink_config.json (refresh interval)"
echo ""
echo "Next steps:"
echo "1. Test display: python src/eink_display.py --once"
echo "2. Start services: sudo systemctl start sports-server.service sports-display.service"