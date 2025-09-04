// Data loading and management
import { mapApiTeamName } from './teams.js';
import { renderGames, updateHeaderTitle } from './renderer.js';

// Test data will be loaded from files
let mlbTestData = [];
let nflTestData = [];
let cfbTestData = [];

// Load test data from files
export async function loadTestData() {
  try {
    const [mlbResponse, nflResponse, cfbResponse] = await Promise.all([
      fetch('/static/test-data/mlb.json'),
      fetch('/static/test-data/nfl.json'),
      fetch('/static/test-data/cfb.json'),
    ]);

    mlbTestData = await mlbResponse.json();
    nflTestData = await nflResponse.json();
    cfbTestData = await cfbResponse.json();
  } catch (error) {
    // Skip over error
  }
}

export function loadMLBData() {
  updateHeaderTitle('MLB');
  renderGames(mlbTestData);
}

export function loadNFLData() {
  updateHeaderTitle('NFL');
  renderGames(nflTestData, 'nfl');
}

export function loadCFBData() {
  updateHeaderTitle('CFB');
  renderGames(cfbTestData, 'cfb');
}

export async function fetchLiveData() {
  // Try to fetch MLB data first
  const league = 'MLB';

  try {
    // Try to fetch from dev server if running
    const response = await fetch(`/api/scores/${league}`);
    if (response.ok) {
      const data = await response.json();

      // Apply favorite team prioritization (Seattle Mariners)
      const favoriteTeam = 'Seattle Mariners';
      const prioritizedData = [...data];

      // Find favorite team game and move to front (check both API and mapped names)
      const favoriteGameIndex = prioritizedData.findIndex(
        (game) =>
          game.home_team === favoriteTeam ||
          game.away_team === favoriteTeam ||
          mapApiTeamName(game.home_team) === 'Mariners' ||
          mapApiTeamName(game.away_team) === 'Mariners'
      );

      if (favoriteGameIndex > 0) {
        const favoriteGame = prioritizedData.splice(favoriteGameIndex, 1)[0];
        prioritizedData.unshift(favoriteGame);
      }

      updateHeaderTitle(league);
      renderGames(prioritizedData);
      console.log('Loaded live data:', prioritizedData);
    } else {
      // Fall back to sample data
      console.log('Dev server not running, using MLB sample data');
      loadMLBData();
    }
  } catch (error) {
    // Dev server not running, use sample data
    console.log('Dev server not available, using MLB sample data');
    loadMLBData();
  }
}
