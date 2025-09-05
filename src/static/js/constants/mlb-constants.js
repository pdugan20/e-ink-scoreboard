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

// Initialize config on module load
async function initGameStatusConfig() {
  try {
    const response = await fetch('/src/config/game-status-config.json');
    gameStatusConfig = await response.json();
    console.log('Game status config loaded:', gameStatusConfig.activeGameStatuses);
  } catch (error) {
    console.error('Could not load game status config:', error);
    // Keep the hardcoded fallback
    gameStatusConfig = {
      activeGameStatuses: ['top ', 'bottom ', 'bot ', 'mid ', 'in progress', 'delay', 'warmup', 'pre-game']
    };
  }
}

// Initialize immediately when module loads
initGameStatusConfig();

export function getMLBActiveGameStatuses() {
  return gameStatusConfig?.activeGameStatuses || ['top ', 'bottom ', 'bot ', 'mid ', 'in progress', 'delay', 'warmup', 'pre-game'];
}