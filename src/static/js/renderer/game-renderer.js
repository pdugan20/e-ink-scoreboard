// Game rendering and display logic
import {
  favoriteTeams,
  currentTheme,
  LEAGUES,
  GAME_STATUS,
  FEATURE_FLAGS,
} from '../config.js';
import {
  MLB_STATUS_PATTERNS,
  getMLBActiveGameStatuses,
} from '../constants/mlb-constants.js';
import {
  mapApiTeamName,
  getTeamLogo,
  generateGradientBackground,
  convertTimeToTimezone,
  formatGameStatus,
} from '../utils/teams.js';
import { generateBaseballDiamondComponent } from '../diamond.js';
import { themeManager } from '../theme-manager.js';
import { updateCurrentTime, updateTimeForGameStart } from './time-renderer.js';
import {
  tryShowScreensaver,
  showNoGamesMessage,
} from './screensaver-renderer.js';

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
  const display = document.getElementById('display');
  const header = document.getElementById('header');

  container.innerHTML = '';

  // Restore header if it was hidden (from screensaver mode)
  if (header) {
    header.style.display = '';
  }

  // Remove screensaver mode class
  display.classList.remove('screensaver-mode');

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
    // Check if screensaver is enabled, and if so, try to show it instead of no-games message
    if (FEATURE_FLAGS.SHOW_SCREENSAVER) {
      tryShowScreensaver(league);
      return;
    }

    // Show "There are no games scheduled for today" message
    showNoGamesMessage();
    return;
  }

  // Sort games to show favorite team first if playing
  const sortedGames = sortGamesByFavorite(games, league);

  // Dynamic game limit based on display size
  const isExpanded = display?.classList.contains('expanded');
  const maxGames = isExpanded ? 30 : 15; // 5x6 for expanded, 3x5 for normal
  const displayGames = sortedGames.slice(0, maxGames);

  // Check if we should show "Games start at" message
  const hasActiveGames = displayGames.some((game) => {
    const status = game.status?.toLowerCase() || '';
    return getMLBActiveGameStatuses().some((activeStatus) =>
      status.includes(activeStatus)
    );
  });

  // Check if any games have already finished (indicating the day's games have begun)
  const hasFinishedGames = displayGames.some((game) => {
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
      gameEl.style.setProperty(
        '--diamond-base-filled-dynamic',
        'var(--color-white-90)'
      );
      gameEl.style.setProperty(
        '--diamond-base-empty-dynamic',
        'var(--color-white-30)'
      );
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
                ${generateBaseballDiamondComponent(game, themeManager.shouldUseDynamicDiamond(shouldApplyDynamicColors), convertTimeToTimezone(formatGameStatus(game.status)))}
            </div>
        `;

    container.appendChild(gameEl);
  });
}

export function sortGamesByFavorite(games, league) {
  // Sort games to prioritize favorite teams
  return games.sort((a, b) => {
    const aHasFavorite =
      isFavoriteTeam(a.away_team, league) ||
      isFavoriteTeam(a.home_team, league);
    const bHasFavorite =
      isFavoriteTeam(b.away_team, league) ||
      isFavoriteTeam(b.home_team, league);

    if (aHasFavorite && !bHasFavorite) return -1;
    if (!aHasFavorite && bHasFavorite) return 1;
    return 0;
  });
}
