// Team helper functions
// Constants are loaded from separate files in constants folder

// Helper functions
function getTeamLogo(teamName, league = 'mlb', useDynamicLogo = false) {
  if (league === 'mlb') {
    // Check for white logo when dynamic colors are enabled
    if (useDynamicLogo && mlbUseWhiteLogos && mlbUseWhiteLogos.includes(teamName)) {
      // Check for special filename override
      const logoFilename = mlbWhiteLogoOverrides[teamName] || mlbTeamLogos[teamName];
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

function getTeamColor(teamName, league = 'mlb', colorType = 'primary') {
  if (league === 'mlb' && mlbTeamColors[teamName]) {
    return (
      mlbTeamColors[teamName][colorType] || mlbTeamColors[teamName].primary
    );
  }
  return '#666666'; // Default gray fallback
}

function getGradientColor(teamName, league = 'mlb') {
  // Check if there's an override for this team's gradient color
  if (league === 'mlb' && mlbGradientColors && mlbGradientColors[teamName]) {
    return getTeamColor(teamName, league, mlbGradientColors[teamName]);
  }
  // Default to primary color
  return getTeamColor(teamName, league, 'primary');
}

function generateGradientBackground(awayTeam, homeTeam, league = 'mlb') {
  // Get the appropriate color for each team (with overrides)
  const awayColor = getGradientColor(awayTeam, league);
  const homeColor = getGradientColor(homeTeam, league);

  // Diagonal gradient with 15 degree angle, colors blend in the center
  // Away team on left, home team on right (matching the display order)
  // Adding 90% opacity to lighten the colors slightly
  return `linear-gradient(105deg, ${awayColor}E6 0%, ${awayColor}E6 25%, ${homeColor}E6 75%, ${homeColor}E6 100%)`;
}
