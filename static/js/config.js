// Configuration and feature flags

// Favorite team configuration
export const favoriteTeams = {
  mlb: 'Mariners',
  nfl: null,
  cfb: null,
};

// Timezone configuration
export const displayTimezone = 'America/Los_Angeles'; // PT timezone, change to your preferred timezone
// Common options: 'America/New_York' (ET), 'America/Chicago' (CT), 'America/Denver' (MT), 'America/Los_Angeles' (PT)

// Feature flags
export const dynamicColors = true;
export const dynamicColorsOnlyFavorites = true; // Only apply dynamic colors to games with favorite teams
