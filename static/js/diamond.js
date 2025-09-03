// Baseball Diamond Component
// Renders a baseball diamond showing base runners and outs

export function generateBaseballDiamondComponent(game, isDynamicColors = false, gameStatus = '') {
  // Only show diamond for live games with bases/outs data
  if (!game.bases || game.outs === undefined) {
    // For final games, show diamond with F in center
    const isFinal = gameStatus === 'Final';
    if (isFinal) {
      const finalDiamond = `
        <img src="assets/icons/${isDynamicColors ? 'diamond-alt-white.png' : 'diamond-alt.png'}" alt="Diamond" class="final-diamond-png">
      `;
      return `
        <div class="baseball-diamond-component">
          <div class="diamond-wrapper">${finalDiamond}</div>
          <div class="game-status">${gameStatus}</div>
        </div>
      `;
    }
    
    // For scheduled games, show venue if available, otherwise show status
    const isScheduled = gameStatus.includes('PM') || gameStatus.includes('AM');
    
    // Debug: Check if venue exists
    if (isScheduled && !game.venue) {
      console.log('Missing venue for scheduled game:', game);
    }
    
    const displayText = game.venue && isScheduled 
      ? `${gameStatus}<br><small>${game.venue}</small>` 
      : gameStatus;
    const alignmentClass = isScheduled ? 'scheduled-game' : '';
    return displayText ? `<div class="baseball-diamond-component ${alignmentClass}"><div class="game-status">${displayText}</div></div>` : '';
  }

  const { first, second, third } = game.bases;
  const outs = game.outs;
  
  // Generate SVG with dynamic base fills
  const diamondSvg = `
    <svg width="24" height="17" viewBox="0 0 35 25" fill="none" xmlns="http://www.w3.org/2000/svg" class="baseball-diamond-svg">
      <!-- Second base (top diamond) -->
      <path d="M15.7549 2.1265C16.4837 1.54673 17.5163 1.54673 18.2451 2.1265L23.0325 5.93483C24.039 6.73554 24.039 8.26446 23.0325 9.06517L18.2451 12.8735C17.5163 13.4533 16.4837 13.4533 15.7549 12.8735L10.9675 9.06517C9.96099 8.26446 9.96099 6.73554 10.9675 5.93483L15.7549 2.1265Z" fill="${second ? (isDynamicColors ? 'rgba(255,255,255,0.9)' : '#999999') : (isDynamicColors ? 'rgba(255,255,255,0.3)' : '#D9D9D9')}"/>
      
      <!-- First base (right diamond) -->
      <path d="M25.2549 10.8765C25.9837 10.2967 27.0163 10.2967 27.7451 10.8765L32.5325 14.6848C33.539 15.4855 33.539 17.0145 32.5325 17.8152L27.7451 21.6235C27.0163 22.2033 25.9837 22.2033 25.2549 21.6235L20.4675 17.8152C19.461 17.0145 19.461 15.4855 20.4675 14.6848L25.2549 10.8765Z" fill="${first ? (isDynamicColors ? 'rgba(255,255,255,0.9)' : '#999999') : (isDynamicColors ? 'rgba(255,255,255,0.3)' : '#D9D9D9')}"/>
      
      <!-- Third base (left diamond) -->
      <path d="M6.25491 10.8765C6.98373 10.2967 8.01626 10.2967 8.74508 10.8765L13.5325 14.6848C14.539 15.4855 14.539 17.0145 13.5325 17.8152L8.74508 21.6235C8.01626 22.2033 6.98373 22.2033 6.25491 21.6235L1.46754 17.8152C0.460988 17.0145 0.96099 15.4855 1.46754 14.6848L6.25491 10.8765Z" fill="${third ? (isDynamicColors ? 'rgba(255,255,255,0.9)' : '#999999') : (isDynamicColors ? 'rgba(255,255,255,0.3)' : '#D9D9D9')}"/>
    </svg>
  `;

  // Generate outs indicators
  const outDots = Array.from({ length: 3 }, (_, i) => {
    const isFilled = i < outs;
    const dynamicClass = isDynamicColors ? ' dynamic' : '';
    const filledClass = isFilled ? ' filled' : '';
    return `<div class="out-dot${dynamicClass}${filledClass}"></div>`;
  }).join('');

  return `
    <div class="baseball-diamond-component">
      <div class="diamond-wrapper">
        ${diamondSvg}
      </div>
      <div class="outs-indicator">
        ${outDots}
      </div>
      ${gameStatus ? `<div class="game-status">${gameStatus}</div>` : ''}
    </div>
  `;
}