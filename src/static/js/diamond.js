// Baseball Diamond Component
// Renders a baseball diamond showing base runners and outs
import { themeManager } from './theme-manager.js';
import { FEATURE_FLAGS } from './config.js';

// Helper function to get CSS variable values
function getCSSVariable(variableName) {
  return getComputedStyle(document.documentElement).getPropertyValue(variableName).trim();
}

function formatInningsStatus(status, isDynamicColors = false) {
  const isEinkOptimized = FEATURE_FLAGS.EINK_OPTIMIZED_CONTRAST && document.body.classList.contains('eink-optimized');
  // Replace "Top" with upward arrow and "Bottom" with downward arrow
  if (status.startsWith('Top ')) {
    const inning = status.replace('Top ', '');
    const arrowColor = isDynamicColors 
      ? getCSSVariable('--diamond-arrow-dynamic')
      : isEinkOptimized
        ? getCSSVariable('--eink-text')
        : getCSSVariable('--diamond-arrow-regular');
    return `<span class="inning-arrow"><svg width="6" height="5" viewBox="0 0 7 6" fill="none" xmlns="http://www.w3.org/2000/svg" style="display: inline-block; margin-right: 2px; vertical-align: middle;"><path d="M2.63398 0.499999C3.01888 -0.166668 3.98113 -0.166667 4.36603 0.5L6.53109 4.25C6.91599 4.91667 6.43486 5.75 5.66506 5.75H1.33493C0.565135 5.75 0.084011 4.91667 0.468911 4.25L2.63398 0.499999Z" fill="${arrowColor}"/></svg></span>${inning}`;
  }
  
  if (status.startsWith('Bottom ')) {
    const inning = status.replace('Bottom ', '');
    const arrowColor = isDynamicColors 
      ? getCSSVariable('--diamond-arrow-dynamic')
      : isEinkOptimized
        ? getCSSVariable('--eink-text')
        : getCSSVariable('--diamond-arrow-regular');
    return `<span class="inning-arrow"><svg width="6" height="5" viewBox="0 0 7 6" fill="none" xmlns="http://www.w3.org/2000/svg" style="display: inline-block; margin-right: 2px; margin-bottom: 1px; vertical-align: middle; transform: rotate(180deg);"><path d="M2.63398 0.499999C3.01888 -0.166668 3.98113 -0.166667 4.36603 0.5L6.53109 4.25C6.91599 4.91667 6.43486 5.75 5.66506 5.75H1.33493C0.565135 5.75 0.084011 4.91667 0.468911 4.25L2.63398 0.499999Z" fill="${arrowColor}"/></svg></span>${inning}`;
  }
  
  
  // Handle "Bot " format (test data)
  if (status.startsWith('Bot ')) {
    const inning = status.replace('Bot ', '');
    const arrowColor = isDynamicColors 
      ? getCSSVariable('--diamond-arrow-dynamic')
      : isEinkOptimized
        ? getCSSVariable('--eink-text')
        : getCSSVariable('--diamond-arrow-regular');
    return `<span class="inning-arrow"><svg width="6" height="5" viewBox="0 0 7 6" fill="none" xmlns="http://www.w3.org/2000/svg" style="display: inline-block; margin-right: 2px; margin-bottom: 1px; vertical-align: middle; transform: rotate(180deg);"><path d="M2.63398 0.499999C3.01888 -0.166668 3.98113 -0.166667 4.36603 0.5L6.53109 4.25C6.91599 4.91667 6.43486 5.75 5.66506 5.75H1.33493C0.565135 5.75 0.084011 4.91667 0.468911 4.25L2.63398 0.499999Z" fill="${arrowColor}"/></svg></span>${inning}`;
  }
  
  // Replace "Middle" with "Mid" for shorter display
  return status.replace('Middle ', 'Mid ');
}

export function generateBaseballDiamondComponent(game, isDynamicColors = false, gameStatus = '') {
  // Treat "Game Over" as "Final"
  if (gameStatus === 'Game Over') {
    gameStatus = 'Final';
  }
  
  // Only show diamond for live games with bases/outs data
  if (!game.bases || game.outs === undefined) {
    // For final games, show diamond with F in center
    const isFinal = gameStatus === 'Final';
    if (isFinal) {
      const isEinkOptimized = FEATURE_FLAGS.EINK_OPTIMIZED_CONTRAST && themeManager.currentTheme === 'default';
      const diamondIcon = isDynamicColors 
        ? 'final-transparent.png'
        : isEinkOptimized 
          ? 'final-legible.png'
          : 'final.png';
          
      const finalDiamond = `
        <img src="assets/icons/${diamondIcon}" alt="Diamond" class="final-diamond-png">
      `;
      // Add theme-specific class for spacing
      const themeClass = (themeManager.currentTheme === 'mlb_scoreboard' || themeManager.currentTheme === 'team_colors') 
        ? ' mlb-scoreboard-spacing' 
        : ' default-spacing';
      
      return `
        <div class="baseball-diamond-component${themeClass}">
          <div class="diamond-wrapper">${finalDiamond}</div>
          <div class="game-status">${formatInningsStatus(gameStatus, isDynamicColors)}</div>
        </div>
      `;
    }
    
    // For scheduled games, show venue if available, otherwise show status
    const isScheduled = gameStatus.includes('PM') || gameStatus.includes('AM');
    
    // Debug: Check if venue exists
    if (isScheduled && !game.venue) {
      console.log('Missing venue for scheduled game:', game);
    }
    
    const formattedStatus = formatInningsStatus(gameStatus, isDynamicColors);
    const displayText = game.venue && isScheduled 
      ? `${formattedStatus}<br><small>${game.venue}</small>` 
      : formattedStatus;
    const alignmentClass = isScheduled ? 'scheduled-game' : '';
    return displayText ? `<div class="baseball-diamond-component ${alignmentClass}"><div class="game-status">${displayText}</div></div>` : '';
  }

  const { first, second, third } = game.bases;
  const outs = game.outs;
  
  // Get base colors from CSS variables
  const isMLBScoreboard = themeManager.isMLBScoreboard();
  const isEinkOptimized = FEATURE_FLAGS.EINK_OPTIMIZED_CONTRAST && themeManager.currentTheme === 'default';
  
  const baseFilledColor = isMLBScoreboard 
    ? getCSSVariable('--mlb-scoreboard-base-filled')
    : isDynamicColors 
      ? getCSSVariable('--diamond-base-filled-dynamic')
      : isEinkOptimized 
        ? getCSSVariable('--eink-optimized-filled')
        : getCSSVariable('--diamond-base-filled');
        
  const baseEmptyColor = isMLBScoreboard
    ? getCSSVariable('--mlb-scoreboard-base-empty')
    : isDynamicColors 
      ? getCSSVariable('--diamond-base-empty-dynamic')
      : isEinkOptimized
        ? getCSSVariable('--eink-optimized-empty')  
        : getCSSVariable('--diamond-base-empty');
  
  // Generate SVG with dynamic base fills
  const diamondSvg = `
    <svg width="24" height="17" viewBox="0 0 35 25" fill="none" xmlns="http://www.w3.org/2000/svg" class="baseball-diamond-svg">
      <!-- Second base (top diamond) -->
      <path d="M15.7549 2.1265C16.4837 1.54673 17.5163 1.54673 18.2451 2.1265L23.0325 5.93483C24.039 6.73554 24.039 8.26446 23.0325 9.06517L18.2451 12.8735C17.5163 13.4533 16.4837 13.4533 15.7549 12.8735L10.9675 9.06517C9.96099 8.26446 9.96099 6.73554 10.9675 5.93483L15.7549 2.1265Z" fill="${second ? baseFilledColor : baseEmptyColor}"/>
      
      <!-- First base (right diamond) -->
      <path d="M25.2549 10.8765C25.9837 10.2967 27.0163 10.2967 27.7451 10.8765L32.5325 14.6848C33.539 15.4855 33.539 17.0145 32.5325 17.8152L27.7451 21.6235C27.0163 22.2033 25.9837 22.2033 25.2549 21.6235L20.4675 17.8152C19.461 17.0145 19.461 15.4855 20.4675 14.6848L25.2549 10.8765Z" fill="${first ? baseFilledColor : baseEmptyColor}"/>
      
      <!-- Third base (left diamond) -->
      <path d="M6.25491 10.8765C6.98373 10.2967 8.01626 10.2967 8.74508 10.8765L13.5325 14.6848C14.539 15.4855 14.539 17.0145 13.5325 17.8152L8.74508 21.6235C8.01626 22.2033 6.98373 22.2033 6.25491 21.6235L1.46754 17.8152C0.460988 17.0145 0.96099 15.4855 1.46754 14.6848L6.25491 10.8765Z" fill="${third ? baseFilledColor : baseEmptyColor}"/>
    </svg>
  `;

  // Generate outs indicators
  const outDots = Array.from({ length: 3 }, (_, i) => {
    const isFilled = i < outs;
    const themeClass = isMLBScoreboard ? ' mlb-scoreboard' : isDynamicColors ? ' dynamic' : '';
    const filledClass = isFilled ? ' filled' : '';
    return `<div class="out-dot${themeClass}${filledClass}"></div>`;
  }).join('');

  return `
    <div class="baseball-diamond-component">
      <div class="diamond-wrapper">
        ${diamondSvg}
      </div>
      <div class="outs-indicator">
        ${outDots}
      </div>
      ${gameStatus ? `<div class="game-status">${formatInningsStatus(gameStatus, isDynamicColors)}</div>` : ''}
    </div>
  `;
}