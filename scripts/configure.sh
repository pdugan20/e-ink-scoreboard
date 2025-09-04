#!/bin/bash
# Interactive configuration for Sports Scores E-ink Display

set -e

echo "⚙️  Sports Scores Display Configuration"
echo "====================================="
echo ""

# Function to update JavaScript config
update_js_config() {
    local file="$1"
    local key="$2" 
    local value="$3"
    
    # Update JavaScript config files
    sed -i "s/export const $key = .*/export const $key = $value;/" "$file"
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

echo "🏈 Choose your favorite MLB team (will appear first when playing):"
echo ""
echo " 1) None                         11) Astros"
echo " 2) D-backs                      12) Royals"  
echo " 3) Braves                       13) Angels"
echo " 4) Orioles                      14) Dodgers"
echo " 5) Red Sox                      15) Marlins"
echo " 6) Cubs                         16) Brewers"
echo " 7) White Sox                    17) Twins"
echo " 8) Reds                         18) Mets"
echo " 9) Guardians                    19) Yankees"
echo "10) Rockies                      20) Athletics"
echo ""
echo "21) Phillies                     26) Mariners"
echo "22) Pirates                      27) Giants"
echo "23) Padres                       28) Cardinals"
echo "24) Rays                         29) Rangers"
echo "25) Blue Jays                    30) Nationals"
echo ""

read -p "Enter choice (1-30): " team_choice

# Map choice to team name (use the short names from the config)
case $team_choice in
    1) favorite_team="null" ;;
    2) favorite_team="'D-backs'" ;;
    3) favorite_team="'Braves'" ;;
    4) favorite_team="'Orioles'" ;;
    5) favorite_team="'Red Sox'" ;;
    6) favorite_team="'Cubs'" ;;
    7) favorite_team="'White Sox'" ;;
    8) favorite_team="'Reds'" ;;
    9) favorite_team="'Guardians'" ;;
    10) favorite_team="'Rockies'" ;;
    11) favorite_team="'Astros'" ;;
    12) favorite_team="'Royals'" ;;
    13) favorite_team="'Angels'" ;;
    14) favorite_team="'Dodgers'" ;;
    15) favorite_team="'Marlins'" ;;
    16) favorite_team="'Brewers'" ;;
    17) favorite_team="'Twins'" ;;
    18) favorite_team="'Mets'" ;;
    19) favorite_team="'Yankees'" ;;
    20) favorite_team="'Athletics'" ;;
    21) favorite_team="'Phillies'" ;;
    22) favorite_team="'Pirates'" ;;
    23) favorite_team="'Padres'" ;;
    24) favorite_team="'Rays'" ;;
    25) favorite_team="'Blue Jays'" ;;
    26) favorite_team="'Mariners'" ;;
    27) favorite_team="'Giants'" ;;
    28) favorite_team="'Cardinals'" ;;
    29) favorite_team="'Rangers'" ;;
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
    1) timezone="TIMEZONES.EASTERN" ;;
    2) timezone="TIMEZONES.CENTRAL" ;;
    3) timezone="TIMEZONES.ARIZONA" ;;
    4) timezone="TIMEZONES.HAWAII" ;;
    5) timezone="TIMEZONES.MOUNTAIN" ;;
    6) timezone="TIMEZONES.PACIFIC" ;;
    7) timezone="'America/Toronto'" ;;
    8) 
        echo ""
        read -p "Enter timezone (e.g., Europe/London): " custom_tz
        timezone="'$custom_tz'"
        ;;
    *) echo "Invalid choice, using US/Eastern"; timezone="TIMEZONES.EASTERN" ;;
esac

echo "✅ Set timezone: $timezone"
update_js_config "src/static/js/config.js" "displayTimezone" "$timezone"

echo ""
echo "🕒 Choose refresh interval:"
echo ""
echo " 1) 2 minutes (120s) - Live game action"
echo " 2) 5 minutes (300s) - Active games" 
echo " 3) 15 minutes (900s) - General use"
echo " 4) 30 minutes (1800s) - Conservative"
echo " 5) 1 hour (3600s) - Minimal updates"
echo ""

read -p "Enter choice (1-5): " interval_choice

case $interval_choice in
    1) interval=120 ;;
    2) interval=300 ;;
    3) interval=900 ;;
    4) interval=1800 ;;
    5) interval=3600 ;;
    *) echo "Invalid choice, using 2 minutes"; interval=120 ;;
esac

echo "✅ Set refresh interval: $interval seconds"
update_json_config "refresh_interval" "$interval"

echo ""
echo "🎨 Choose display theme:"
echo ""
echo " 1) Default - Clean with colorful team logos"
echo " 2) Team Colors - Dynamic team color backgrounds"
echo " 3) MLB Scoreboard - Classic scoreboard appearance"
echo ""

read -p "Enter choice (1-3): " theme_choice

case $theme_choice in
    1) theme="THEMES.DEFAULT" ;;
    2) theme="THEMES.TEAM_COLORS" ;;
    3) theme="THEMES.MLB_SCOREBOARD" ;;
    *) echo "Invalid choice, using default"; theme="THEMES.DEFAULT" ;;
esac

echo "✅ Set theme: $theme"
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