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

// Hardcoded fallback (MUST match src/config/game-status-config.json!)
const FALLBACK_ACTIVE_STATUSES = ['top ', 'bottom ', 'bot ', 'mid ', 'middle ', 'end ', 'in progress', 'delay', 'warmup', 'pre-game', 'suspended'];

// Initialize config on module load
async function initGameStatusConfig() {
  try {
    const response = await fetch('/src/config/game-status-config.json');
    gameStatusConfig = await response.json();
    console.log('Game status config loaded:', gameStatusConfig.activeGameStatuses);
    
    // Validate that JSON and fallback are in sync
    const jsonStatuses = [...gameStatusConfig.activeGameStatuses].sort();
    const fallbackStatuses = [...FALLBACK_ACTIVE_STATUSES].sort();
    
    if (JSON.stringify(jsonStatuses) !== JSON.stringify(fallbackStatuses)) {
      console.error('⚠️ WARNING: JSON config and JavaScript fallback are out of sync!');
      console.error('JSON config:', jsonStatuses);
      console.error('JS fallback:', fallbackStatuses);
      console.error('Please update both src/config/game-status-config.json and mlb-constants.js FALLBACK_ACTIVE_STATUSES');
    } else {
      console.log('✅ JSON config and JavaScript fallback are in sync');
    }
  } catch (error) {
    console.error('Could not load game status config:', error);
    // Keep the hardcoded fallback
    gameStatusConfig = {
      activeGameStatuses: FALLBACK_ACTIVE_STATUSES
    };
  }
}

// Initialize immediately when module loads
initGameStatusConfig();

export function getMLBActiveGameStatuses() {
  return gameStatusConfig?.activeGameStatuses || FALLBACK_ACTIVE_STATUSES;
}