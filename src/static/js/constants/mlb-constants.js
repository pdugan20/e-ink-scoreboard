// MLB-specific constants

// MLB team name mapping (API names to display names)
export const MLB_TEAM_NAME_MAP = {
  'Arizona Diamondbacks': 'D-backs',
  'Atlanta Braves': 'Braves',
  'Baltimore Orioles': 'Orioles',
  'Boston Red Sox': 'Red Sox',
  'Chicago Cubs': 'Cubs',
  'Chicago White Sox': 'White Sox',
  'Cincinnati Reds': 'Reds',
  'Cleveland Guardians': 'Guardians',
  'Colorado Rockies': 'Rockies',
  'Detroit Tigers': 'Tigers',
  'Houston Astros': 'Astros',
  'Kansas City Royals': 'Royals',
  'Los Angeles Angels': 'Angels',
  'Los Angeles Dodgers': 'Dodgers',
  'Miami Marlins': 'Marlins',
  'Milwaukee Brewers': 'Brewers',
  'Minnesota Twins': 'Twins',
  'New York Mets': 'Mets',
  'New York Yankees': 'Yankees',
  'Oakland Athletics': 'Athletics',
  'Philadelphia Phillies': 'Phillies',
  'Pittsburgh Pirates': 'Pirates',
  'San Diego Padres': 'Padres',
  'San Francisco Giants': 'Giants',
  'Seattle Mariners': 'Mariners',
  'St. Louis Cardinals': 'Cardinals',
  'Tampa Bay Rays': 'Rays',
  'Texas Rangers': 'Rangers',
  'Toronto Blue Jays': 'Blue Jays',
  'Washington Nationals': 'Nationals',
};

// MLB game status patterns
export const MLB_STATUS_PATTERNS = {
  PM_ET: 'PM ET',
  AM_ET: 'AM ET',
};

// Load active game statuses from shared JSON config
let gameStatusConfig = null;

export async function getMLBActiveGameStatuses() {
  if (!gameStatusConfig) {
    try {
      const response = await fetch('/src/config/game-status-config.json');
      gameStatusConfig = await response.json();
    } catch (error) {
      logger.error('Could not load game status config:', error);
      throw error;
    }
  }
  return gameStatusConfig.activeGameStatuses;
}

// For backwards compatibility, export the constant synchronously
// This will need to be updated to use the async function above
export const MLB_ACTIVE_GAME_STATUSES = [
  'top ',
  'bottom ',
  'bot ',
  'mid ',
  'in progress',
  'delay',
  'warmup',
  'pre-game'
];