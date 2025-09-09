// Theme Manager - Centralized theme logic
import { THEMES } from './config.js';

// Theme configurations
const themeConfigs = {
  [THEMES.DEFAULT]: {
    name: 'default',
    bodyClass: 'theme-default',
    showLogos: true,
    dynamicColors: (hasFavoriteTeam) => hasFavoriteTeam,
    useDynamicDiamond: false,
    hideLogosForMLBScoreboard: false,
  },
  [THEMES.TEAM_COLORS]: {
    name: 'team-colors',
    bodyClass: 'theme-team-colors',
    showLogos: true,
    dynamicColors: () => true,
    useDynamicDiamond: false,
    hideLogosForMLBScoreboard: false,
  },
  [THEMES.MLB_SCOREBOARD]: {
    name: 'mlb-scoreboard',
    bodyClass: 'theme-mlb-scoreboard',
    showLogos: false,
    dynamicColors: () => false,
    useDynamicDiamond: true,
    hideLogosForMLBScoreboard: true,
  },
};

class ThemeManager {
  constructor() {
    this.currentTheme = null;
    this.config = null;
  }

  setTheme(theme) {
    this.currentTheme = theme;
    this.config = themeConfigs[theme];

    // Remove all theme classes
    Object.values(themeConfigs).forEach((config) => {
      document.body.classList.remove(config.bodyClass);
    });

    // Add current theme class
    if (this.config) {
      document.body.classList.add(this.config.bodyClass);
    }
  }

  shouldUseDynamicColors(hasFavoriteTeam) {
    return this.config ? this.config.dynamicColors(hasFavoriteTeam) : false;
  }

  shouldShowLogos() {
    return this.config ? this.config.showLogos : true;
  }

  shouldUseDynamicDiamond(hasDynamicColors) {
    return this.config
      ? this.config.useDynamicDiamond || hasDynamicColors
      : hasDynamicColors;
  }

  isMLBScoreboard() {
    return this.currentTheme === THEMES.MLB_SCOREBOARD;
  }

  getThemeClass() {
    return this.config ? this.config.name : '';
  }
}

// Export singleton instance
export const themeManager = new ThemeManager();
