// Data loading and management
import { renderGames, updateHeaderTitle } from './renderer.js';

// Test data will be loaded from files
let mlbTestData = [];
let mlbScheduledData = [];
let mlbEmptyData = [];
let nflTestData = [];
let cfbTestData = [];

// Load test data from files
export async function loadTestData() {
  try {
    const [
      mlbResponse,
      mlbScheduledResponse,
      mlbEmptyResponse,
      nflResponse,
      cfbResponse,
    ] = await Promise.all([
      fetch('/static/test-data/mlb.json'),
      fetch('/static/test-data/mlb-scheduled.json'),
      fetch('/static/test-data/mlb-empty.json'),
      fetch('/static/test-data/nfl.json'),
      fetch('/static/test-data/cfb.json'),
    ]);

    mlbTestData = await mlbResponse.json();
    mlbScheduledData = await mlbScheduledResponse.json();
    mlbEmptyData = await mlbEmptyResponse.json();
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

export function loadMLBScheduledData() {
  updateHeaderTitle('MLB');
  renderGames(mlbScheduledData);
}

export function loadMLBEmptyData() {
  updateHeaderTitle('MLB');
  renderGames(mlbEmptyData);
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

      // Apply favorite team prioritization using the configured favorites
      const { sortGamesByFavorite } = await import('./renderer.js');
      const prioritizedData = sortGamesByFavorite(data, league);

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

export async function loadScreensaverData() {
  try {
    // Try to fetch screensaver data from dev server for MLB (could be made configurable later)
    const league = 'mlb';
    const response = await fetch(`/api/screensaver/${league}`);
    if (response.ok) {
      const data = await response.json();
      // Update header title based on the team or use a generic title
      const headerTitle = data.team ? `${data.team} News` : 'Team News';
      updateHeaderTitle(headerTitle);
      const { renderScreensaver } = await import('./renderer.js');
      renderScreensaver(data);
      console.log('Loaded screensaver data:', data);
    } else {
      console.log('Dev server not running, cannot load screensaver');
    }
  } catch (error) {
    console.log('Dev server not available, cannot load screensaver');
  }
}
