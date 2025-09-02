import js from '@eslint/js';

export default [
  js.configs.recommended,
  {
    files: ['static/js/**/*.js'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'script',
      globals: {
        // Browser globals
        window: 'readonly',
        document: 'readonly',
        console: 'readonly',
        fetch: 'readonly',
        setInterval: 'readonly',
        Date: 'readonly',
        parseInt: 'readonly',
        
        // Custom globals from config.js
        favoriteTeams: 'readonly',
        dynamicColors: 'readonly',
        dynamicColorsOnlyFavorites: 'readonly',
        
        // Custom globals from constants
        mlbTeamLogos: 'readonly',
        mlbUseWhiteLogos: 'readonly',
        mlbWhiteLogoOverrides: 'readonly',
        mlbTeamColors: 'readonly',
        mlbGradientColors: 'readonly',
        getTeamLogo: 'readonly',
        getTeamColor: 'readonly',
        generateGradientBackground: 'readonly',
        
        // Custom globals from renderer.js
        renderGames: 'readonly',
        sortGamesByFavorite: 'readonly',
        updateHeaderTitle: 'readonly',
        updateCurrentTime: 'readonly',
        updateSizeIndicator: 'readonly',
        
        // Custom globals from data.js
        mlbTestData: 'writable',
        nflTestData: 'writable',
        cfbTestData: 'writable',
        loadTestData: 'readonly',
        loadMLBData: 'readonly',
        loadNFLData: 'readonly',
        loadCFBData: 'readonly',
        fetchLiveData: 'readonly',
        
        // Custom globals from controls.js
        targetWidth: 'writable',
        targetHeight: 'writable',
        toggleDevTray: 'readonly',
        setSize: 'readonly',
        initApp: 'readonly'
      }
    },
    rules: {
      'no-unused-vars': 'off', // Variables are used across script files
      'no-console': 'off',
      'prefer-const': 'warn',
      'no-redeclare': 'off' // Variables are intentionally global across scripts
    }
  }
];