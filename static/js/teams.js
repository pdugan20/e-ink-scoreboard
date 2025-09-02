// Team helper functions
import { displayTimezone } from './config.js';
import { mlbTeamLogos } from './constants/mlb-logos.js';
import { mlbUseWhiteLogos, mlbWhiteLogoOverrides } from './constants/mlb-secondary-logos.js';
import { mlbTeamColors } from './constants/mlb-colors.js';
import { mlbGradientColors } from './constants/mlb-gradient-colors.js';

// Map API team names to our internal team names
export function mapApiTeamName(apiTeamName, league = 'mlb') {
  if (league === 'mlb') {
    const mlbNameMap = {
      'Arizona Diamondbacks': 'Diamondbacks',
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
  }
  return apiTeamName;
}

// Helper functions  
export function getTeamLogo(teamName, league = 'mlb', useDynamicLogo = false) {
  if (league === 'mlb') {
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

export function getTeamColor(teamName, league = 'mlb', colorType = 'primary') {
  if (league === 'mlb' && mlbTeamColors[teamName]) {
    return (
      mlbTeamColors[teamName][colorType] || mlbTeamColors[teamName].primary
    );
  }
  return '#666666'; // Default gray fallback
}

export function getGradientColor(teamName, league = 'mlb') {
  // Check if there's an override for this team's gradient color
  if (league === 'mlb' && mlbGradientColors && mlbGradientColors[teamName]) {
    return getTeamColor(teamName, league, mlbGradientColors[teamName]);
  }
  // Default to primary color
  return getTeamColor(teamName, league, 'primary');
}

export function generateGradientBackground(awayTeam, homeTeam, league = 'mlb') {
  // Get the appropriate color for each team (with overrides)
  const awayColor = getGradientColor(awayTeam, league);
  const homeColor = getGradientColor(homeTeam, league);

  // Diagonal gradient with 15 degree angle, colors blend in the center
  // Away team on left, home team on right (matching the display order)
  // Adding 90% opacity to lighten the colors slightly
  return `linear-gradient(105deg, ${awayColor}E6 0%, ${awayColor}E6 25%, ${homeColor}E6 75%, ${homeColor}E6 100%)`;
}

export function convertTimeToTimezone(timeString) {
  // Convert ET times to the configured timezone
  // Input format: "10:40 PM ET" or "11:35 PM ET"
  if (!timeString.includes('ET')) {
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

    if (period === 'PM' && hour24 !== 12) {
      hour24 += 12;
    } else if (period === 'AM' && hour24 === 12) {
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
    let displayPeriod = 'AM';

    if (convertedHour === 0) {
      displayHour = 12;
      displayPeriod = 'AM';
    } else if (convertedHour < 12) {
      displayHour = convertedHour;
      displayPeriod = 'AM';
    } else if (convertedHour === 12) {
      displayHour = 12;
      displayPeriod = 'PM';
    } else {
      displayHour = convertedHour - 12;
      displayPeriod = 'PM';
    }

    // Get timezone abbreviation
    const timezoneAbbrev = getTimezoneAbbreviation(displayTimezone);

    return `${displayHour}:${minutes.padStart(2, '0')} ${displayPeriod} ${timezoneAbbrev}`;
  } catch (error) {
    console.warn('Error converting timezone:', error);
    return timeString; // Return original on error
  }
}

export function getTimezoneAbbreviation(timezone) {
  const abbreviations = {
    'America/New_York': 'ET',
    'America/Chicago': 'CT',
    'America/Denver': 'MT',
    'America/Los_Angeles': 'PT',
    'America/Phoenix': 'MST',
    'America/Anchorage': 'AKT',
    'Pacific/Honolulu': 'HST',
  };

  return abbreviations[timezone] || timezone.split('/').pop();
}
