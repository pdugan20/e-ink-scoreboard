// Configuration and feature flags

// Feature flags
export const FEATURE_FLAGS = {
  SHOW_STANDINGS: false,
  EINK_OPTIMIZED_CONTRAST: true,
  SHOW_SCREENSAVER: true,
};

// Favorite team configuration
export const favoriteTeams = {
  mlb: ['Seattle Mariners'],
  nfl: null,
  cfb: null,
};

// Timezone constants
export const TIMEZONES = {
  EASTERN: 'America/New_York',
  CENTRAL: 'America/Chicago',
  MOUNTAIN: 'America/Denver',
  PACIFIC: 'America/Los_Angeles',
  ARIZONA: 'America/Phoenix',
  ALASKA: 'America/Anchorage',
  HAWAII: 'Pacific/Honolulu',
};

// Timezone configuration
export const displayTimezone = TIMEZONES.PACIFIC;

// Theme constants
export const THEMES = {
  DEFAULT: 'default',
  TEAM_COLORS: 'team_colors',
  MLB_SCOREBOARD: 'mlb_scoreboard',
};

// Theme configuration
export const currentTheme = THEMES.DEFAULT;

// League constants
export const LEAGUES = {
  MLB: 'mlb',
  NFL: 'nfl',
  CFB: 'cfb',
};

// Game status constants
export const GAME_STATUS = {
  FINAL: 'Final',
};

// Time constants
export const TIME_PERIODS = {
  AM: 'AM',
  PM: 'PM',
  ET: 'ET',
};

// Color type constants
export const COLOR_TYPES = {
  PRIMARY: 'primary',
  SECONDARY: 'secondary',
  TERTIARY: 'tertiary',
};

// Day names
export const DAYS = [
  'Sunday',
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
];

// Month names
export const MONTHS = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
];

// Timezone abbreviations
export const TIMEZONE_ABBREVIATIONS = {
  'America/New_York': 'ET',
  'America/Chicago': 'CT',
  'America/Denver': 'MT',
  'America/Los_Angeles': 'PT',
  'America/Phoenix': 'MST',
  'America/Anchorage': 'AKT',
  'Pacific/Honolulu': 'HST',
};
