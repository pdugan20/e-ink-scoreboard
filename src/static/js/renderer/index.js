// Main renderer exports - combines all rendering modules
export { renderGames, sortGamesByFavorite } from './game-renderer.js';
export {
  renderScreensaver,
  tryShowScreensaver,
  showNoGamesMessage,
} from './screensaver-renderer.js';
export {
  updateHeaderTitle,
  updateCurrentTime,
  updateTimeForGameStart,
  updateSizeIndicator,
} from './time-renderer.js';
