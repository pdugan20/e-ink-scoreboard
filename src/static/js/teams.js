// Team helper functions
import { displayTimezone, LEAGUES, TIME_PERIODS, COLOR_TYPES, TIMEZONE_ABBREVIATIONS } from './config.js';
import { MLB_TEAM_NAME_MAP } from './constants/mlb-constants.js';
import { mlbTeamLogos } from './constants/mlb-logos.js';
import {
  mlbUseWhiteLogos,
  mlbWhiteLogoOverrides,
} from './constants/mlb-secondary-logos.js';
import { mlbTeamColors } from './constants/mlb-colors.js';
import { mlbGradientColors } from './constants/mlb-gradient-colors.js';

// Map API team names to our internal team names
<<<<<<< HEAD:static/js/teams.js
export function mapApiTeamName(apiTeamName, league = 'mlb') {
  if (league === 'mlb') {
    const mlbNameMap = {
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

    return mlbNameMap[apiTeamName] || apiTeamName;
=======
export function mapApiTeamName(apiTeamName, league = LEAGUES.MLB) {
  if (league === LEAGUES.MLB) {
    return MLB_TEAM_NAME_MAP[apiTeamName] || apiTeamName;
>>>>>>> baseball-diamond-feature:src/static/js/teams.js
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

export function getGradientColor(teamName, league = LEAGUES.MLB) {
  // Check if there's an override for this team's gradient color
  if (league === LEAGUES.MLB && mlbGradientColors && mlbGradientColors[teamName]) {
    return getTeamColor(teamName, league, mlbGradientColors[teamName]);
  }
  // Default to primary color
  return getTeamColor(teamName, league, COLOR_TYPES.PRIMARY);
}

export function generateGradientBackground(awayTeam, homeTeam, league = LEAGUES.MLB) {
  // Get the appropriate color for each team (with overrides)
  const awayColor = getGradientColor(awayTeam, league);
  const homeColor = getGradientColor(homeTeam, league);

  // Diagonal gradient with 15 degree angle, colors blend in the center
  // Away team on left, home team on right (matching the display order)
  // Adding 90% opacity to lighten the colors slightly
  return `linear-gradient(105deg, ${awayColor}E6 0%, ${awayColor}E6 25%, ${homeColor}E6 75%, ${homeColor}E6 100%)`;
}

export function formatGameStatus(statusString, gameData = null) {
  let formattedStatus = statusString;
  
  // Convert "Bottom" to "Bot" for brevity
  if (statusString.includes('Bottom ')) {
    formattedStatus = statusString.replace('Bottom ', 'Bot ');
  }
  
  // Add middot and outs for active games
  if (gameData && (statusString.includes('Top ') || statusString.includes('Bottom ') || statusString.includes('Bot ')) && gameData.outs !== undefined) {
    const outs = gameData.outs || 0;
    formattedStatus += ` · ${outs} out${outs === 1 ? '' : 's'}`;
  }
  
  // Convert ET times to configured timezone, or return as-is
  return convertTimeToTimezone(formattedStatus);
}

export function convertTimeToTimezone(timeString) {
  // Convert ET times to the configured timezone
  // Input format: "10:40 PM ET" or "11:35 PM ET"
  if (!timeString.includes(TIME_PERIODS.ET)) {
    return timeString; // Return as-is if not an ET time
  }

  try {
    // Extract the time part and remove ET
    const timeMatch = timeString.match(/(\d{1,2}:\d{2}\s+[AP]M)\s+ET/);
    if (!timeMatch) {
      return timeString; // Return original if can't parse
    }

    const timeStr = timeMatch[1];

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
