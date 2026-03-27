/* global AbortController, clearTimeout */

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
  // Set fake date for test mode (Saturday, August 16 at 4:30 PM ET)
  window.testDate = new Date('2025-08-16T16:30:00-04:00');
  updateHeaderTitle('MLB');
  renderGames(mlbTestData);
}

export function loadMLBScheduledData() {
  window.testDate = new Date('2025-08-16T11:00:00-04:00');
  updateHeaderTitle('MLB');
  renderGames(mlbScheduledData);
}

export function loadMLBEmptyData() {
  window.testDate = new Date('2025-02-10T12:00:00-05:00');
  updateHeaderTitle('MLB');
  renderGames(mlbEmptyData);
}

export function loadNFLData() {
  window.testDate = new Date('2025-10-12T16:00:00-04:00');
  updateHeaderTitle('NFL');
  renderGames(nflTestData, 'nfl');
}

export function loadCFBData() {
  window.testDate = new Date('2025-10-11T15:00:00-04:00');
  updateHeaderTitle('CFB');
  renderGames(cfbTestData, 'cfb');
}

export async function fetchLiveData() {
  window.testDate = null;
  const league = 'MLB';

  try {
    // Try to fetch from API with longer timeout for slow Pi
    // Use AbortController if available (modern browsers)
    const fetchOptions = {};
    let timeoutId;

    if (typeof AbortController !== 'undefined') {
      const controller = new AbortController();
      timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout
      fetchOptions.signal = controller.signal;
    }

    const response = await fetch(`/api/scores/${league}`, fetchOptions);

    if (timeoutId) {
      clearTimeout(timeoutId);
    }

    if (response.ok) {
      const data = await response.json();

      // Apply favorite team prioritization using the configured favorites
      const { sortGamesByFavorite } = await import('./renderer.js');
      const prioritizedData = sortGamesByFavorite(data, league);

      updateHeaderTitle(league);
      renderGames(prioritizedData);
      console.log('Loaded live data:', prioritizedData);
    } else {
      // Show error message
      console.error('API returned error:', response.status);
      updateHeaderTitle('Error Loading Scores');
      document.getElementById('games').innerHTML =
        '<div style="padding: 20px; text-align: center;">Failed to load scores (HTTP ' +
        response.status +
        ')</div>';
    }
  } catch (error) {
    // Show error message
    console.error('Error fetching scores:', error);
    updateHeaderTitle('Connection Error');
    document.getElementById('games').innerHTML =
      '<div style="padding: 20px; text-align: center;">Unable to connect to API server</div>';
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
