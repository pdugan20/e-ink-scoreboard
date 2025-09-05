// Game rendering and display logic
import {
  favoriteTeams,
  currentTheme,
  LEAGUES,
  GAME_STATUS,
  DAYS,
  MONTHS,
  FEATURE_FLAGS,
} from './config.js';
import { MLB_STATUS_PATTERNS, getMLBActiveGameStatuses } from './constants/mlb-constants.js';
import {
  mapApiTeamName,
  getTeamLogo,
  generateGradientBackground,
  convertTimeToTimezone,
} from './teams.js';
import { generateBaseballDiamondComponent } from './diamond.js';
import { themeManager } from './theme-manager.js';

// Helper function to check if a team is in the favorite teams list
function isFavoriteTeam(teamName, league) {
  const favoriteTeamList = favoriteTeams[league];
  
  if (!favoriteTeamList) {
    return false;
  }
  
  // Handle both string and array formats
  if (Array.isArray(favoriteTeamList)) {
    return favoriteTeamList.includes(teamName);
  } else {
    return favoriteTeamList === teamName;
  }
}

export function renderGames(games, league = LEAGUES.MLB) {
  const container = document.getElementById('games');
  container.innerHTML = '';

  // Apply e-ink optimized contrast only for default theme
  if (FEATURE_FLAGS.EINK_OPTIMIZED_CONTRAST && currentTheme === 'default') {
    document.body.classList.add('eink-optimized');
  } else {
    document.body.classList.remove('eink-optimized');
  }

  // Initialize theme manager
  themeManager.setTheme(currentTheme);

  // Check for empty games array
  if (!games || games.length === 0) {
    // Show "There are no games scheduled for today" message
    const noGamesEl = document.createElement('div');
    noGamesEl.className = 'no-games-message';
    noGamesEl.textContent = 'There are no games scheduled for today';
    container.appendChild(noGamesEl);
    updateCurrentTime(''); // Empty string to hide the time text entirely
    return;
  }

  // Sort games to show favorite team first if playing
  const sortedGames = sortGamesByFavorite(games, league);

  // Limit to maximum 15 games (3x5 grid)
  const maxGames = 15;
  const displayGames = sortedGames.slice(0, maxGames);

  // Check if we should show "Games start at" message
  const hasActiveGames = displayGames.some(game => {
    const status = game.status?.toLowerCase() || '';
    return getMLBActiveGameStatuses().some(activeStatus => status.includes(activeStatus));
  });

  // Check if any games have already finished (indicating the day's games have begun)
  const hasFinishedGames = displayGames.some(game => {
    const status = game.status?.toLowerCase() || '';
    return status.includes('final') || status.includes('game over');
  });

  if (!hasActiveGames && !hasFinishedGames) {
    // No active games and no finished games - show "Games start at" for first game
    updateTimeForGameStart(displayGames);
  } else {
    // Either active games or games have already started today - use "Last update at"
    updateCurrentTime();
  }

  displayGames.forEach((game) => {
    const gameEl = document.createElement('div');
    gameEl.className = 'game-pill';

    // Map API team names to short names for logos/colors
    const awayTeamMapped = mapApiTeamName(game.away_team, league);
    const homeTeamMapped = mapApiTeamName(game.home_team, league);

    // Check if this game has any favorite team
    const hasFavoriteTeam =
      isFavoriteTeam(game.away_team, league) ||
      isFavoriteTeam(game.home_team, league);

    // Apply dynamic colors based on theme
    const shouldApplyDynamicColors =
      themeManager.shouldUseDynamicColors(hasFavoriteTeam);

    if (shouldApplyDynamicColors) {
      const gradientBg = generateGradientBackground(
        awayTeamMapped,
        homeTeamMapped,
        league
      );
      gameEl.style.background = gradientBg;
      gameEl.classList.add('dynamic-colors');
      
      // Update CSS variables for diamond colors when dynamic colors are applied
      gameEl.style.setProperty('--diamond-base-filled-dynamic', 'var(--color-white-90)');
      gameEl.style.setProperty('--diamond-base-empty-dynamic', 'var(--color-white-30)');
    }

    // Add theme class
    const themeClass = themeManager.getThemeClass();
    if (themeClass) {
      gameEl.classList.add(themeClass);
    }

    // Use secondary logos when dynamic colors are applied to this game (use mapped names)
    const showLogos = themeManager.shouldShowLogos();
    const awayLogo = showLogos
      ? getTeamLogo(awayTeamMapped, league, shouldApplyDynamicColors)
      : null;
    const homeLogo = showLogos
      ? getTeamLogo(homeTeamMapped, league, shouldApplyDynamicColors)
      : null;

    // Check game status and scores
    const isFinal =
      game.status === GAME_STATUS.FINAL || game.status === 'Game Over';
    const isScheduled =
      game.status.includes(MLB_STATUS_PATTERNS.PM_ET) ||
      game.status.includes(MLB_STATUS_PATTERNS.AM_ET);
    const awayScore = parseInt(game.away_score);
    const homeScore = parseInt(game.home_score);
    const awayLosing = isFinal && awayScore < homeScore;
    const homeLosing = isFinal && homeScore < awayScore;

    gameEl.innerHTML = `
            <div class="matchup">
                <div class="teams-and-scores">
                    <div class="team-row">
                        <div class="team-info">
                            ${awayLogo ? `<img src="${awayLogo}" alt="${awayTeamMapped}" class="team-logo">` : ''}
                            <div class="team-details">
                                <div class="team-name">${awayTeamMapped} ${FEATURE_FLAGS.SHOW_STANDINGS && game.away_record ? `<span class="team-record">${game.away_record}</span>` : ''}</div>
                            </div>
                        </div>
                        ${isScheduled ? '<div class="score-placeholder"></div>' : `<div class="score${awayLosing ? ' losing-score' : ''}">${game.away_score}</div>`}
                    </div>
                    <div class="team-row">
                        <div class="team-info">
                            ${homeLogo ? `<img src="${homeLogo}" alt="${homeTeamMapped}" class="team-logo">` : ''}
                            <div class="team-details">
                                <div class="team-name">${homeTeamMapped} ${FEATURE_FLAGS.SHOW_STANDINGS && game.home_record ? `<span class="team-record">${game.home_record}</span>` : ''}</div>
                            </div>
                        </div>
                        ${isScheduled ? '<div class="score-placeholder"></div>' : `<div class="score${homeLosing ? ' losing-score' : ''}">${game.home_score}</div>`}
                    </div>
                </div>
                ${generateBaseballDiamondComponent(game, themeManager.shouldUseDynamicDiamond(shouldApplyDynamicColors), convertTimeToTimezone(game.status))}
            </div>
        `;
    container.appendChild(gameEl);
  });
}

export function sortGamesByFavorite(games, league) {
  const favoriteTeamList = favoriteTeams[league];

  if (!favoriteTeamList) {
    return games; // No favorite team set for this league
  }

  // Find games where any favorite team is playing
  const favoriteGames = games.filter(
    (game) => 
      isFavoriteTeam(game.away_team, league) || 
      isFavoriteTeam(game.home_team, league)
  );

  // Get all other games
  const otherGames = games.filter(
    (game) => 
      !isFavoriteTeam(game.away_team, league) && 
      !isFavoriteTeam(game.home_team, league)
  );

  // Return favorite team games first, then other games
  return [...favoriteGames, ...otherGames];
}

export function updateHeaderTitle(league) {
  const now = new Date();

  const dayName = DAYS[now.getDay()];
  const monthName = MONTHS[now.getMonth()];
  const dayNum = now.getDate();

  document.getElementById('header-title').textContent =
    `${league} Scores for ${dayName}, ${monthName} ${dayNum}`;
  updateCurrentTime();
}

export function updateCurrentTime(customText = null) {
  const now = new Date();
  let hours = now.getHours();
  const minutes = now.getMinutes().toString().padStart(2, '0');
  const ampm = hours >= 12 ? 'PM' : 'AM';
  hours = hours % 12;
  hours = hours ? hours : 12; // 0 should be 12

  const timeString = `${hours}:${minutes} ${ampm}`;
  const displayText = customText !== null ? customText : `Last update at ${timeString}`;
  
  document.getElementById('current-time').textContent = displayText;
}

export function updateTimeForGameStart(games) {
  // Find the earliest scheduled game
  const scheduledGames = games.filter(game => {
    const status = game.status?.toLowerCase() || '';
    return status.includes('pm et') || status.includes('am et') || status.includes('scheduled');
  });

  if (scheduledGames.length === 0) {
    updateCurrentTime(); // Default to regular update time
    return;
  }

  // Find the earliest game time
  let earliestTime = null;
  let earliestGame = null;

  scheduledGames.forEach(game => {
    const status = game.status || '';
    // Extract time from status like "7:30 PM ET"
    const timeMatch = status.match(/(\d{1,2}):(\d{2})\s*(AM|PM)/i);
    if (timeMatch) {
      const [, hourStr, minuteStr, ampm] = timeMatch;
      let hour24 = parseInt(hourStr);
      const minute = parseInt(minuteStr);
      
      if (ampm.toUpperCase() === 'PM' && hour24 !== 12) {
        hour24 += 12;
      } else if (ampm.toUpperCase() === 'AM' && hour24 === 12) {
        hour24 = 0;
      }
      
      const gameTime = hour24 * 60 + minute; // Convert to minutes for comparison
      
      if (earliestTime === null || gameTime < earliestTime) {
        earliestTime = gameTime;
        earliestGame = game;
      }
    }
  });

  if (earliestGame) {
    // Convert the time to user's timezone before displaying
    const convertedTime = convertTimeToTimezone(earliestGame.status);
    // Extract just the time part from the converted result
    const timeMatch = convertedTime.match(/(\d{1,2}:\d{2}\s*(?:AM|PM))/i);
    if (timeMatch) {
      const gameTimeStr = timeMatch[1];
      updateCurrentTime(`Games start at ${gameTimeStr}`);
      return;
    }
  }

  // Fallback to regular update time
  updateCurrentTime();
}

export function updateSizeIndicator() {
  // Import targetWidth and targetHeight from controls.js when needed
  const targetWidth = window.targetWidth || 800;
  const targetHeight = window.targetHeight || 480;
  document.getElementById('size-indicator').textContent =
    `${targetWidth} x ${targetHeight}`;
}
