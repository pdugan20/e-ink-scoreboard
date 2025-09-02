// Data loading and management

// Test data will be loaded from files
let mlbTestData = [];
let nflTestData = [];
let cfbTestData = [];

// Load test data from files
async function loadTestData() {
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

function loadMLBData() {
  updateHeaderTitle('MLB');
  renderGames(mlbTestData);
}

function loadNFLData() {
  updateHeaderTitle('NFL');
  renderGames(nflTestData, 'nfl');
}

function loadCFBData() {
  updateHeaderTitle('CFB');
  renderGames(cfbTestData, 'cfb');
}

async function fetchLiveData() {
  // Try to fetch MLB data first
  const league = 'MLB';

  try {
    // Try to fetch from dev server if running
    const response = await fetch(`/api/scores/${league}`);
    if (response.ok) {
      const data = await response.json();
      updateHeaderTitle(league);
      renderGames(data);
      console.log('Loaded live data:', data);
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
