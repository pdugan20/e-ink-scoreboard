// Team helper functions
import { displayTimezone, LEAGUES, TIME_PERIODS, COLOR_TYPES, TIMEZONE_ABBREVIATIONS } from '../config.js';
import { MLB_TEAM_NAME_MAP } from '../constants/mlb-constants.js';
import { mlbTeamLogos } from '../constants/mlb-logos.js';
import {
  mlbUseWhiteLogos,
  mlbWhiteLogoOverrides,
} from '../constants/mlb-secondary-logos.js';
import { mlbTeamColors } from '../constants/mlb-colors.js';
import { getBestGradientColors } from './gradient-color-optimizer.js';

// Map API team names to our internal team names
export function mapApiTeamName(apiTeamName, league = LEAGUES.MLB) {
  if (league === LEAGUES.MLB) {
    return MLB_TEAM_NAME_MAP[apiTeamName] || apiTeamName;
  }
  return apiTeamName;
}

// Helper functions
export function getTeamLogo(teamName, league = LEAGUES.MLB, useDynamicLogo = false) {
  if (league === LEAGUES.MLB) {
    // Check for white logo when dynamic colors are enabled
    if (
      useDynamicLogo &&
      mlbUseWhiteLogos &&
      mlbUseWhiteLogos.includes(teamName)
    ) {
      // Check for special filename override, otherwise use same filename as regular logo
      const logoFilename =
        mlbWhiteLogoOverrides[teamName] || mlbTeamLogos[teamName];
      if (logoFilename) {
        return `/assets/logos/mlb-white/${logoFilename}.png`;
      }
    }
    // Use default logo
    if (mlbTeamLogos[teamName]) {
      return `/assets/logos/mlb/${mlbTeamLogos[teamName]}.png`;
    }
  }
  return null;
}

export function getTeamColor(teamName, league = LEAGUES.MLB, colorType = COLOR_TYPES.PRIMARY) {
  if (league === LEAGUES.MLB && mlbTeamColors[teamName]) {
    return (
      mlbTeamColors[teamName][colorType] || mlbTeamColors[teamName].primary
    );
  }
  return 'var(--color-gray-600)'; // Default gray fallback
}

export function generateGradientBackground(awayTeam, homeTeam, league = LEAGUES.MLB) {
  if (league !== LEAGUES.MLB) {
    // For non-MLB leagues, fall back to primary colors
    const awayColor = getTeamColor(awayTeam, league, COLOR_TYPES.PRIMARY);
    const homeColor = getTeamColor(homeTeam, league, COLOR_TYPES.PRIMARY);
    return `linear-gradient(105deg, ${awayColor}E6 0%, ${awayColor}E6 25%, ${homeColor}E6 75%, ${homeColor}E6 100%)`;
  }
  
  // Get team color objects
  const awayTeamColors = mlbTeamColors[awayTeam];
  const homeTeamColors = mlbTeamColors[homeTeam];
  
  if (!awayTeamColors || !homeTeamColors) {
    // Fallback if team colors not found
    const awayColor = getTeamColor(awayTeam, league, COLOR_TYPES.PRIMARY);
    const homeColor = getTeamColor(homeTeam, league, COLOR_TYPES.PRIMARY);
    return `linear-gradient(105deg, ${awayColor}E6 0%, ${awayColor}E6 25%, ${homeColor}E6 75%, ${homeColor}E6 100%)`;
  }
  
  // Use dynamic optimization to get best colors
  const optimizedColors = getBestGradientColors(awayTeamColors, homeTeamColors);
  
  // Diagonal gradient with 15 degree angle, colors blend in the center
  // Away team on left, home team on right (matching the display order)
  // Adding 90% opacity to lighten the colors slightly
  return `linear-gradient(105deg, ${optimizedColors.team1Color}E6 0%, ${optimizedColors.team1Color}E6 25%, ${optimizedColors.team2Color}E6 75%, ${optimizedColors.team2Color}E6 100%)`;
}

export function convertTimeToTimezone(timeString) {
  // Convert ET times to the configured timezone and strip timezone markers
  // Input format: "10:40 PM ET"
  
  // If no timezone marker found, return as-is
  if (!timeString.includes('ET')) {
    return timeString;
  }

  try {
    // Legacy ET conversion logic (keeping for compatibility)
    const etMatch = timeString.match(/(\d{1,2}:\d{2}\s+[AP]M)\s+ET/);
    if (!etMatch) {
      return timeString; // Return original if can't parse
    }

    const timeStr = etMatch[1];

    // Parse the ET time
    const [time, period] = timeStr.split(' ');
    const [hours, minutes] = time.split(':');
    let hour24 = parseInt(hours);

    if (period === TIME_PERIODS.PM && hour24 !== 12) {
      hour24 += 12;
    } else if (period === TIME_PERIODS.AM && hour24 === 12) {
      hour24 = 0;
    }

    // Simple timezone offset conversion
    // ET to other timezones (assuming standard time, not DST)
    let hourOffset = 0;
    if (displayTimezone === 'America/Los_Angeles') {
      // PT
      hourOffset = -3; // PT is 3 hours behind ET
    } else if (displayTimezone === 'America/Denver') {
      // MT
      hourOffset = -2; // MT is 2 hours behind ET
    } else if (displayTimezone === 'America/Chicago') {
      // CT
      hourOffset = -1; // CT is 1 hour behind ET
    }
    // ET stays the same (hourOffset = 0)

    // Apply the offset
    let convertedHour = hour24 + hourOffset;

    // Handle day overflow/underflow
    if (convertedHour < 0) {
      convertedHour += 24;
    } else if (convertedHour >= 24) {
      convertedHour -= 24;
    }

    // Convert back to 12-hour format
    let displayHour = convertedHour;
    let displayPeriod = TIME_PERIODS.AM;

    if (convertedHour === 0) {
      displayHour = 12;
      displayPeriod = TIME_PERIODS.AM;
    } else if (convertedHour < 12) {
      displayHour = convertedHour;
      displayPeriod = TIME_PERIODS.AM;
    } else if (convertedHour === 12) {
      displayHour = 12;
      displayPeriod = TIME_PERIODS.PM;
    } else {
      displayHour = convertedHour - 12;
      displayPeriod = TIME_PERIODS.PM;
    }

    return `${displayHour}:${minutes.padStart(2, '0')} ${displayPeriod}`;
  } catch (error) {
    console.warn('Error converting timezone:', error);
    return timeString; // Return original on error
  }
}

export function getTimezoneAbbreviation(timezone) {
  return TIMEZONE_ABBREVIATIONS[timezone] || timezone.split('/').pop();
}

export function formatGameStatus(status) {
  // Clean up long status messages for better display
  const lowerStatus = status.toLowerCase();
  
  if (lowerStatus.includes('manager challenge')) {
    return 'Challenge';
  }
  
  if (lowerStatus.includes('instant replay')) {
    return 'Replay';
  }
  
  if (lowerStatus.includes('rain delay') || lowerStatus.includes('weather delay')) {
    return 'Delay';
  }
  
  if (lowerStatus.includes('commercial break')) {
    return 'Break';
  }
  
  if (lowerStatus.includes('pitching change')) {
    return 'Sub';
  }
  
  // Add other status cleanups as needed
  return status;
}
