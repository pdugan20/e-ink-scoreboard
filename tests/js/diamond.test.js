/**
 * Tests for baseball diamond rendering component
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { generateBaseballDiamondComponent } from '@/diamond.js';

// Mock the theme-manager module
vi.mock('@/theme-manager.js', () => ({
  themeManager: {
    currentTheme: 'default',
    isMLBScoreboard: () => false,
  },
}));

// Mock the config module
vi.mock('@/config.js', () => ({
  FEATURE_FLAGS: {
    EINK_OPTIMIZED_CONTRAST: false,
  },
}));

// Mock CSS variables
const mockCSSVariables = {
  '--diamond-base-filled': '#FFD700',
  '--diamond-base-empty': '#808080',
  '--diamond-arrow-regular': '#000000',
  '--diamond-base-filled-dynamic': '#FF0000',
  '--diamond-base-empty-dynamic': '#CCCCCC',
  '--diamond-arrow-dynamic': '#0000FF',
  '--eink-text': '#000000',
  '--eink-optimized-filled': '#000000',
  '--eink-optimized-empty': '#FFFFFF',
};

beforeEach(() => {
  // Mock getComputedStyle
  global.getComputedStyle = vi.fn(() => ({
    getPropertyValue: (prop) => mockCSSVariables[prop] || '',
  }));

  // Mock document.body
  document.body.className = '';
});

describe('generateBaseballDiamondComponent', () => {
  describe('Live games with bases and outs', () => {
    it('should render diamond with all bases empty and zero outs', () => {
      const game = {
        bases: { first: false, second: false, third: false },
        outs: 0,
      };

      const result = generateBaseballDiamondComponent(game);

      expect(result).toContain('baseball-diamond-component');
      expect(result).toContain('baseball-diamond-svg');
      expect(result).toContain('outs-indicator');
      // Check for empty base color
      expect(result).toContain('#808080');
    });

    it('should render diamond with runner on first base', () => {
      const game = {
        bases: { first: true, second: false, third: false },
        outs: 1,
      };

      const result = generateBaseballDiamondComponent(game);

      expect(result).toContain('baseball-diamond-svg');
      // Check for filled base color (first base)
      expect(result).toContain('#FFD700');
      // Check for empty base color (second and third)
      expect(result).toContain('#808080');
    });

    it('should render diamond with bases loaded', () => {
      const game = {
        bases: { first: true, second: true, third: true },
        outs: 2,
      };

      const result = generateBaseballDiamondComponent(game);

      expect(result).toContain('baseball-diamond-svg');
      // All bases should use filled color
      const filledCount = (result.match(/#FFD700/g) || []).length;
      expect(filledCount).toBe(3); // All three bases filled
    });

    it('should render correct number of out dots', () => {
      const game = {
        bases: { first: false, second: false, third: false },
        outs: 2,
      };

      const result = generateBaseballDiamondComponent(game);

      expect(result).toContain('out-dot');
      // Check for filled class (2 outs) - use non-greedy match
      const filledDots = (result.match(/out-dot[^<]*filled/g) || []).length;
      expect(filledDots).toBe(2);
    });

    it('should show game status for live games', () => {
      const game = {
        bases: { first: true, second: false, third: false },
        outs: 1,
      };

      const result = generateBaseballDiamondComponent(game, false, 'Top 7th');

      expect(result).toContain('game-status');
      expect(result).toContain('7th'); // Status text
    });

    it('should format Top innings with arrow', () => {
      const game = {
        bases: { first: false, second: false, third: false },
        outs: 0,
      };

      const result = generateBaseballDiamondComponent(game, false, 'Top 9th');

      expect(result).toContain('inning-arrow');
      expect(result).toContain('svg');
      expect(result).toContain('9th');
    });

    it('should format Bottom innings with arrow', () => {
      const game = {
        bases: { first: false, second: false, third: false },
        outs: 1,
      };

      const result = generateBaseballDiamondComponent(
        game,
        false,
        'Bottom 5th'
      );

      expect(result).toContain('inning-arrow');
      expect(result).toContain('rotate(180deg)'); // Bottom arrow is rotated
      expect(result).toContain('5th');
    });

    it('should use dynamic colors when isDynamicColors is true', () => {
      const game = {
        bases: { first: true, second: false, third: false },
        outs: 0,
      };

      const result = generateBaseballDiamondComponent(game, true);

      // Should use dynamic color CSS variables
      expect(result).toContain('#FF0000'); // Dynamic filled color
      expect(result).toContain('#CCCCCC'); // Dynamic empty color
    });
  });

  describe('Final games', () => {
    it('should render final diamond for completed games', () => {
      const game = {}; // No bases/outs for final game

      const result = generateBaseballDiamondComponent(game, false, 'Final');

      expect(result).toContain('final-diamond-png');
      expect(result).toContain('final.png');
      expect(result).toContain('game-status');
      expect(result).toContain('Final');
    });

    it('should treat Game Over as Final', () => {
      const game = {};

      const result = generateBaseballDiamondComponent(game, false, 'Game Over');

      expect(result).toContain('final-diamond-png');
      expect(result).toContain('Final');
      expect(result).not.toContain('Game Over');
    });

    it('should use transparent final icon for dynamic colors', () => {
      const game = {};

      const result = generateBaseballDiamondComponent(game, true, 'Final');

      expect(result).toContain('final-transparent.png');
    });
  });

  describe('Scheduled games', () => {
    it('should show game time for scheduled games', () => {
      const game = {
        venue: 'Fenway Park',
      };

      const result = generateBaseballDiamondComponent(
        game,
        false,
        '7:05 PM ET'
      );

      expect(result).toContain('7:05 PM ET');
      expect(result).toContain('Fenway Park');
      expect(result).toContain('scheduled-game');
    });

    it('should show status without venue if venue is missing', () => {
      const game = {};

      const result = generateBaseballDiamondComponent(
        game,
        false,
        '7:05 PM ET'
      );

      expect(result).toContain('7:05 PM ET');
      expect(result).not.toContain('<br>');
    });

    it('should handle AM times', () => {
      const game = {
        venue: 'Wrigley Field',
      };

      const result = generateBaseballDiamondComponent(
        game,
        false,
        '1:20 PM ET'
      );

      expect(result).toContain('1:20 PM ET');
      expect(result).toContain('Wrigley Field');
    });
  });

  describe('Status formatting', () => {
    it('should replace Middle with Mid', () => {
      const game = {
        bases: { first: false, second: false, third: false },
        outs: 0,
      };

      const result = generateBaseballDiamondComponent(
        game,
        false,
        'Middle 3rd'
      );

      expect(result).toContain('Mid 3rd');
      expect(result).not.toContain('Middle');
    });

    it('should handle Bot format', () => {
      const game = {
        bases: { first: true, second: false, third: false },
        outs: 2,
      };

      const result = generateBaseballDiamondComponent(game, false, 'Bot 8th');

      expect(result).toContain('8th');
      expect(result).toContain('rotate(180deg)'); // Bot uses bottom arrow
    });

    it('should simplify Delay status', () => {
      const game = {};

      const result = generateBaseballDiamondComponent(
        game,
        false,
        'Weather Delay'
      );

      expect(result).toContain('Delay');
      expect(result).not.toContain('Weather');
    });
  });

  describe('Edge cases', () => {
    it('should handle missing bases data', () => {
      const game = {};

      const result = generateBaseballDiamondComponent(game);

      // Should not crash, should show empty component or status
      expect(result).toBeDefined();
      expect(typeof result).toBe('string');
    });

    it('should handle 3 outs', () => {
      const game = {
        bases: { first: false, second: false, third: false },
        outs: 3,
      };

      const result = generateBaseballDiamondComponent(game);

      // All 3 out dots should be filled - use non-greedy match
      const filledDots = (result.match(/out-dot[^<]*filled/g) || []).length;
      expect(filledDots).toBe(3);
    });

    it('should return empty string when no game data and no status', () => {
      const game = {};

      const result = generateBaseballDiamondComponent(game, false, '');

      expect(result).toBe('');
    });
  });
});
