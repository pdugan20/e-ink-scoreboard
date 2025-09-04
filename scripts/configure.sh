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

echo "⚾️ Choose your favorite MLB teams (will appear first when playing):"
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

read -p "Enter choices separated by commas (e.g., 2,16,22 or 1 for none): " team_choices

# Function to map number to team name (for JS config)
get_team_name() {
    case $1 in
        1) echo "null" ;;
        2) echo "'Angels'" ;;
        3) echo "'Astros'" ;;
        4) echo "'Athletics'" ;;
        5) echo "'Blue Jays'" ;;
        6) echo "'Guardians'" ;;
        7) echo "'White Sox'" ;;
        8) echo "'Twins'" ;;
        9) echo "'Mariners'" ;;
        10) echo "'Orioles'" ;;
        11) echo "'Rangers'" ;;
        12) echo "'Red Sox'" ;;
        13) echo "'Royals'" ;;
        14) echo "'Rays'" ;;
        15) echo "'Tigers'" ;;
        16) echo "'Yankees'" ;;
        17) echo "'D-backs'" ;;
        18) echo "'Braves'" ;;
        19) echo "'Cubs'" ;;
        20) echo "'Reds'" ;;
        21) echo "'Rockies'" ;;
        22) echo "'Dodgers'" ;;
        23) echo "'Giants'" ;;
        24) echo "'Brewers'" ;;
        25) echo "'Marlins'" ;;
        26) echo "'Mets'" ;;
        27) echo "'Phillies'" ;;
        28) echo "'Pirates'" ;;
        29) echo "'Cardinals'" ;;
        30) echo "'Nationals'" ;;
        *) echo "null" ;;
    esac
}

# Function to map number to readable team name (for display)
get_readable_team_name() {
    case $1 in
        1) echo "" ;;
        2) echo "Angels" ;;
        3) echo "Astros" ;;
        4) echo "Athletics" ;;
        5) echo "Blue Jays" ;;
        6) echo "Guardians" ;;
        7) echo "White Sox" ;;
        8) echo "Twins" ;;
        9) echo "Mariners" ;;
        10) echo "Orioles" ;;
        11) echo "Rangers" ;;
        12) echo "Red Sox" ;;
        13) echo "Royals" ;;
        14) echo "Rays" ;;
        15) echo "Tigers" ;;
        16) echo "Yankees" ;;
        17) echo "D-backs" ;;
        18) echo "Braves" ;;
        19) echo "Cubs" ;;
        20) echo "Reds" ;;
        21) echo "Rockies" ;;
        22) echo "Dodgers" ;;
        23) echo "Giants" ;;
        24) echo "Brewers" ;;
        25) echo "Marlins" ;;
        26) echo "Mets" ;;
        27) echo "Phillies" ;;
        28) echo "Pirates" ;;
        29) echo "Cardinals" ;;
        30) echo "Nationals" ;;
        *) echo "" ;;
    esac
}

# Process multiple team selections
favorite_teams_array=()
readable_teams_array=()
IFS=',' read -ra CHOICES <<< "$team_choices"

for choice in "${CHOICES[@]}"; do
    # Trim whitespace
    choice=$(echo "$choice" | xargs)
    team_name=$(get_team_name "$choice")
    readable_name=$(get_readable_team_name "$choice")
    if [ "$team_name" != "null" ] && [ "$readable_name" != "" ]; then
        favorite_teams_array+=("$team_name")
        readable_teams_array+=("$readable_name")
    fi
done

if [ ${#favorite_teams_array[@]} -gt 0 ]; then
    # Join array elements with commas for JS config
    favorite_teams_str=$(printf "%s," "${favorite_teams_array[@]}")
    favorite_teams_str="[${favorite_teams_str%,}]"  # Remove trailing comma and wrap in brackets
    
    # Create readable display text
    if [ ${#readable_teams_array[@]} -eq 1 ]; then
        readable_display="${readable_teams_array[0]}"
    elif [ ${#readable_teams_array[@]} -eq 2 ]; then
        readable_display="${readable_teams_array[0]} and ${readable_teams_array[1]}"
    else
        # Join all but last with commas, then add "and" before the last
        readable_display=$(printf "%s, " "${readable_teams_array[@]:0:$((${#readable_teams_array[@]}-1))}")
        readable_display="${readable_display%, } and ${readable_teams_array[-1]}"
    fi
    
    echo "✅ Set favorite teams: $readable_display"
    update_js_config "src/static/js/config.js" "favoriteTeams" "{ mlb: $favorite_teams_str, nfl: null, cfb: null }"
else
    echo "✅ No favorite teams selected"
    update_js_config "src/static/js/config.js" "favoriteTeams" "{ mlb: null, nfl: null, cfb: null }"
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
echo " 1) 120 seconds (2 minutes) - Live action"
echo " 2) 300 seconds (5 minutes) - Default, good for active game times" 
echo " 3) 900 seconds (15 minutes) - Balanced for general use"
echo " 4) 1800 seconds (30 minutes) - Conservative, preserves display life"
echo ""

read -p "Enter choice (1-4): " interval_choice

case $interval_choice in
    1) interval=120 ;;
    2) interval=300 ;;
    3) interval=900 ;;
    4) interval=1800 ;;
    *) echo "Invalid choice, using 5 minutes"; interval=300 ;;
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