// Time and header rendering logic
import {
  displayTimezone,
  DAYS,
  MONTHS,
  TIMEZONE_ABBREVIATIONS,
} from '../config.js';
import { convertTimeToTimezone } from '../utils/teams.js';

export function updateHeaderTitle(league) {
  const headerTitle = document.getElementById('header-title');
  const today = new Date();
  const dayName = DAYS[today.getDay()];
  const monthName = MONTHS[today.getMonth()];
  const dayOfMonth = today.getDate();

  if (headerTitle) {
    if (league === 'Mariners News' || league === 'Team News' || league.includes('News')) {
      headerTitle.textContent = league;
    } else {
      headerTitle.textContent = `${league.toUpperCase()} Scores for ${dayName}, ${monthName} ${dayOfMonth}`;
    }
  }
}

export function updateCurrentTime(customText = null) {
  const currentTimeEl = document.getElementById('current-time');
  if (!currentTimeEl) return;

  const now = new Date();
  
  // Convert to display timezone
  const timeOptions = {
    timeZone: displayTimezone,
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  };
  
  const timeString = now.toLocaleTimeString('en-US', timeOptions);
  
  const displayText = customText !== null ? customText : `Last update at ${timeString}`;
  currentTimeEl.textContent = displayText;
}

export function updateTimeForGameStart(games) {
  // Find the earliest scheduled game to show "Games start at" time
  const scheduledGames = games.filter(game => {
    const status = game.status?.toLowerCase() || '';
    return status.includes('pm et') || status.includes('am et') || status.includes('scheduled');
  });

  if (scheduledGames.length === 0) {
    updateCurrentTime();
    return;
  }

  // Find the earliest game time
  let earliestTime = null;
  let earliestGame = null;

  scheduledGames.forEach(game => {
    const status = game.status || '';
    // Extract time from status like "7:30 PM ET"
    const timeMatch = status.match(/(\d{1,2}):(\d{2})\s*(AM|PM)/i);
    if (timeMatch) {
      const [, hourStr, minuteStr, ampm] = timeMatch;
      let hour24 = parseInt(hourStr);
      const minute = parseInt(minuteStr);
      
      if (ampm.toUpperCase() === 'PM' && hour24 !== 12) {
        hour24 += 12;
      } else if (ampm.toUpperCase() === 'AM' && hour24 === 12) {
        hour24 = 0;
      }
      
      const gameTime = hour24 * 60 + minute; // Convert to minutes for comparison
      
      if (earliestTime === null || gameTime < earliestTime) {
        earliestTime = gameTime;
        earliestGame = game;
      }
    }
  });

  if (earliestGame) {
    // Convert the time to user's timezone before displaying
    const convertedTime = convertTimeToTimezone(earliestGame.status);
    // Extract just the time part from the converted result
    const timeMatch = convertedTime.match(/(\d{1,2}:\d{2}\s*(?:AM|PM))/i);
    if (timeMatch) {
      const gameTimeStr = timeMatch[1];
      updateCurrentTime(`Games start at ${gameTimeStr}`);
      return;
    }
  }

  // Fallback to regular update time
  updateCurrentTime();
}

export function updateSizeIndicator() {
  // Import targetWidth and targetHeight from controls.js when needed
  const targetWidth = window.targetWidth || 800;
  const targetHeight = window.targetHeight || 480;
  document.getElementById('size-indicator').textContent =
    `${targetWidth} x ${targetHeight}`;
}