// Dynamic Gradient Color Optimizer
// Automatically selects the best color combination for team vs team gradients
// Prioritizes preferred color harmonies: greens+blues, blue+blue, red+blue, black+blue, green+red

// Colors to never use in gradients
const BANNED_COLOR_FAMILIES = ['white', 'orange', 'yellow'];

const BANNED_COLORS = [
  '#EFD19F', // Giants tertiary
  '#E8291C', // Blue Jays tertiary
];

const COLOR_CLASSIFICATIONS = {
  '#005C5C': 'green', // Mariners primary
  '#003831': 'green', // Athletics primary
  '#13274F': 'blue', // Braves secondary
  '#134A8E': 'blue', // Blue Jays primary
  '#1D2D5C': 'blue', // Blue Jays secondary
  '#003087': 'blue', // Yankees primary
  '#0C2C56': 'blue', // Mariners secondary
  '#005A9C': 'blue', // Dodgers primary
  '#EF3E42': 'red', // Dodgers secondary
  '#27251F': 'black', // Giants secondary
  '#000000': 'black', // D-backs tertiary
};

// Convert hex color to RGB object
function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16),
      }
    : null;
}

// Calculate perceptual color distance using Delta E (simplified)
function getColorDistance(color1, color2) {
  const rgb1 = hexToRgb(color1);
  const rgb2 = hexToRgb(color2);

  if (!rgb1 || !rgb2) return 0;

  // Weighted RGB distance (approximates human color perception)
  const deltaR = rgb1.r - rgb2.r;
  const deltaG = rgb1.g - rgb2.g;
  const deltaB = rgb1.b - rgb2.b;

  return Math.sqrt(
    2 * deltaR * deltaR + 4 * deltaG * deltaG + 3 * deltaB * deltaB
  );
}

// Classify color into basic color families
function getColorFamily(hex) {
  if (COLOR_CLASSIFICATIONS[hex]) {
    return COLOR_CLASSIFICATIONS[hex];
  }

  const rgb = hexToRgb(hex);
  if (!rgb) return 'unknown';

  const { r, g, b } = rgb;
  const brightness = (r * 299 + g * 587 + b * 114) / 1000;

  if (brightness < 15) return 'black';

  if (brightness > 200 && Math.max(r, g, b) - Math.min(r, g, b) < 50)
    return 'white';

  // Determine dominant color
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const saturation = max === 0 ? 0 : (max - min) / max;

  // Low saturation = gray
  if (saturation < 0.3) return brightness < 128 ? 'black' : 'gray';

  // High saturation color classification
  if (r === max) {
    if (g > b * 1.5) return 'orange';
    if (b > g * 1.2) return 'purple';
    return 'red';
  } else if (g === max) {
    if (r > b * 1.2) return 'yellow';
    if (b > r * 1.2) return 'cyan';
    return 'green';
  } else {
    // b === max
    if (r > g * 1.2) return 'purple';
    if (g > r * 1.5) return 'cyan';
    return 'blue';
  }
}

// Check if color combination matches preferred harmonies
function getHarmonyScore(color1, color2) {
  const family1 = getColorFamily(color1);
  const family2 = getColorFamily(color2);

  // NEVER use banned color families - eliminate immediately
  if (
    BANNED_COLOR_FAMILIES.includes(family1) ||
    BANNED_COLOR_FAMILIES.includes(family2)
  ) {
    return 0;
  }

  const combination = [family1, family2].sort().join('+');

  // Preferred harmonies (high score)
  const preferredHarmonies = {
    'blue+green': 100,
    'blue+blue': 95,
    'blue+red': 90,
    'black+blue': 85,
    'black+red': 65,
    'black+green': 60,
  };

  // Good contrasts but not preferred
  const decentHarmonies = {
    'gray+blue': 40,
    'gray+red': 40,
    'gray+green': 35,
    'black+gray': 30,
  };

  // Poor combinations (low score) - white/orange/yellow handled by BANNED_COLOR_FAMILIES
  const poorHarmonies = {
    'red+red': 10,
    'green+green': 10,
    'gray+gray': 5,
  };

  return (
    preferredHarmonies[combination] ||
    decentHarmonies[combination] ||
    poorHarmonies[combination] ||
    30
  ); // Default neutral score
}

// Calculate overall score for a color combination
function scoreColorCombination(color1, color2) {
  const rgb1 = hexToRgb(color1);
  const rgb2 = hexToRgb(color2);

  if (!rgb1 || !rgb2) return 0;

  const brightness1 = (rgb1.r * 299 + rgb1.g * 587 + rgb1.b * 114) / 1000;
  const brightness2 = (rgb2.r * 299 + rgb2.g * 587 + rgb2.b * 114) / 1000;
  const family1 = getColorFamily(color1);
  const family2 = getColorFamily(color2);

  // Check banned families and specific banned colors
  if (
    BANNED_COLOR_FAMILIES.includes(family1) ||
    BANNED_COLOR_FAMILIES.includes(family2) ||
    BANNED_COLORS.includes(color1) ||
    BANNED_COLORS.includes(color2)
  ) {
    return 0; // Completely eliminate these colors
  }

  // REQUIRE dark colors for white text readability (brightness < 120)
  if (brightness1 > 120 || brightness2 > 120) {
    return 0; // Eliminate colors that are too light for white text
  }

  // Bonus for very dark colors (better for white text)
  let darknessBonus = 0;
  if (brightness1 < 80 && brightness2 < 80) {
    darknessBonus = 20; // Both very dark = excellent
  } else if (brightness1 < 80 || brightness2 < 80) {
    darknessBonus = 10; // One very dark = good
  }

  const distance = getColorDistance(color1, color2);
  const harmonyScore = getHarmonyScore(color1, color2);

  // Normalize distance score (0-100, higher is better)
  const distanceScore = Math.min(distance / 5, 100);

  // Weighted final score: harmony + darkness bonus + distance
  return harmonyScore * 0.6 + distanceScore * 0.2 + darknessBonus * 0.2;
}

// Main function to get best gradient colors for two teams
export function getBestGradientColors(team1Colors, team2Colors) {
  const combinations = [
    {
      team1Color: team1Colors.primary,
      team2Color: team2Colors.primary,
      team1Type: 'primary',
      team2Type: 'primary',
    },
    {
      team1Color: team1Colors.primary,
      team2Color: team2Colors.secondary,
      team1Type: 'primary',
      team2Type: 'secondary',
    },
    {
      team1Color: team1Colors.secondary,
      team2Color: team2Colors.primary,
      team1Type: 'secondary',
      team2Type: 'primary',
    },
    {
      team1Color: team1Colors.secondary,
      team2Color: team2Colors.secondary,
      team1Type: 'secondary',
      team2Type: 'secondary',
    },
  ];

  // Add tertiary combinations if they exist
  if (team1Colors.tertiary && team2Colors.tertiary) {
    combinations.push(
      {
        team1Color: team1Colors.primary,
        team2Color: team2Colors.tertiary,
        team1Type: 'primary',
        team2Type: 'tertiary',
      },
      {
        team1Color: team1Colors.tertiary,
        team2Color: team2Colors.primary,
        team1Type: 'tertiary',
        team2Type: 'primary',
      },
      {
        team1Color: team1Colors.secondary,
        team2Color: team2Colors.tertiary,
        team1Type: 'secondary',
        team2Type: 'tertiary',
      },
      {
        team1Color: team1Colors.tertiary,
        team2Color: team2Colors.secondary,
        team1Type: 'tertiary',
        team2Type: 'secondary',
      }
    );
  }

  // Score each combination
  let bestCombination = combinations[0];
  let bestScore = 0;

  for (const combo of combinations) {
    const score = scoreColorCombination(combo.team1Color, combo.team2Color);
    if (score > bestScore) {
      bestScore = score;
      bestCombination = combo;
    }
  }

  return {
    team1Color: bestCombination.team1Color,
    team2Color: bestCombination.team2Color,
    team1ColorType: bestCombination.team1Type,
    team2ColorType: bestCombination.team2Type,
    score: bestScore,
  };
}

// Helper function for backward compatibility with existing code
export function getTeamGradientColor(teamName, teamColors, opponentColors) {
  const result = getBestGradientColors(teamColors, opponentColors);

  // Return which color type this team should use
  return result.team1ColorType;
}
