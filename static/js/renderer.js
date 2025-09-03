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
import { MLB_STATUS_PATTERNS } from './constants/mlb-constants.js';
import {
  mapApiTeamName,
  getTeamLogo,
  generateGradientBackground,
  convertTimeToTimezone,
} from './teams.js';
import { generateBaseballDiamondComponent } from './diamond.js';
import { themeManager } from './theme-manager.js';

export function renderGames(games, league = LEAGUES.MLB) {
  const container = document.getElementById('games');
  container.innerHTML = '';

  // Initialize theme manager
  themeManager.setTheme(currentTheme);

  // Sort games to show favorite team first if playing
  const sortedGames = sortGamesByFavorite(games, league);

  // Limit to maximum 12 games (3x4 grid)
  const maxGames = 12;
  const displayGames = sortedGames.slice(0, maxGames);

  displayGames.forEach((game) => {
    const gameEl = document.createElement('div');
    gameEl.className = 'game-pill';

    // Map API team names to our internal names for lookups
    const awayTeamMapped = mapApiTeamName(game.away_team, league);
    const homeTeamMapped = mapApiTeamName(game.home_team, league);

    // Check if this game has the favorite team (check both API and mapped names)
    const favoriteTeam = favoriteTeams[league];
    const hasFavoriteTeam =
      favoriteTeam &&
      (game.away_team === favoriteTeam ||
        game.home_team === favoriteTeam ||
        awayTeamMapped === favoriteTeam ||
        homeTeamMapped === favoriteTeam);

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
  const favoriteTeam = favoriteTeams[league];

  if (!favoriteTeam) {
    return games; // No favorite team set for this league
  }

  // Find games where favorite team is playing
  const favoriteGames = games.filter(
    (game) => game.away_team === favoriteTeam || game.home_team === favoriteTeam
  );

  // Get all other games
  const otherGames = games.filter(
    (game) => game.away_team !== favoriteTeam && game.home_team !== favoriteTeam
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

export function updateCurrentTime() {
  const now = new Date();
  let hours = now.getHours();
  const minutes = now.getMinutes().toString().padStart(2, '0');
  const ampm = hours >= 12 ? 'PM' : 'AM';
  hours = hours % 12;
  hours = hours ? hours : 12; // 0 should be 12

  document.getElementById('current-time').textContent =
    `${hours}:${minutes} ${ampm}`;
}

export function updateSizeIndicator() {
  // Import targetWidth and targetHeight from controls.js when needed
  const targetWidth = window.targetWidth || 800;
  const targetHeight = window.targetHeight || 400;
  document.getElementById('size-indicator').textContent =
    `${targetWidth} x ${targetHeight}`;
}
