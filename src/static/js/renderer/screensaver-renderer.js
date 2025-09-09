// Screensaver rendering logic
import { updateHeaderTitle, updateCurrentTime } from './time-renderer.js';

export function renderScreensaver(articleData) {
  const container = document.getElementById('games');
  const display = document.getElementById('display');
  const header = document.getElementById('header');

  // Clear existing content
  container.innerHTML = '';

  // Hide the header completely for edge-to-edge display
  if (header) {
    header.style.display = 'none';
  }

  // Remove any existing screensaver styles
  display.classList.remove('screensaver-mode');

  // Create screensaver container that fills the entire display
  const screensaverEl = document.createElement('div');
  screensaverEl.className = 'screensaver-container';

  // Set background image if available
  if (articleData.image_url) {
    screensaverEl.style.backgroundImage = `url(${articleData.image_url})`;
    screensaverEl.style.backgroundSize = 'cover';
    screensaverEl.style.backgroundPosition = 'center';
    screensaverEl.style.backgroundRepeat = 'no-repeat';
  } else {
    // Fallback gradient background
    screensaverEl.style.background =
      'linear-gradient(135deg, #005C5C 0%, #007777 100%)';
  }

  // Add gradient overlay
  const gradientOverlay = document.createElement('div');
  gradientOverlay.className = 'gradient-overlay';

  // Create content container
  const contentEl = document.createElement('div');
  contentEl.className = 'screensaver-content';

  // Article title
  const titleEl = document.createElement('h2');
  titleEl.className = 'article-title';
  titleEl.textContent = articleData.title || 'Team News';

  // Published date
  const dateEl = document.createElement('div');
  dateEl.className = 'article-date';
  dateEl.textContent = articleData.published || '';

  // Article description
  const descriptionEl = document.createElement('p');
  descriptionEl.className = 'article-description';
  descriptionEl.textContent = articleData.description || '';

  // Assemble the content
  contentEl.appendChild(titleEl);
  if (dateEl.textContent) {
    contentEl.appendChild(dateEl);
  }
  if (descriptionEl.textContent) {
    contentEl.appendChild(descriptionEl);
  }

  // Add everything to the screensaver container
  screensaverEl.appendChild(gradientOverlay);
  screensaverEl.appendChild(contentEl);

  // Add to the main container
  container.appendChild(screensaverEl);

  // Add screensaver mode class to display
  display.classList.add('screensaver-mode');

  console.log('Rendered screensaver with article:', articleData.title);
}

export async function tryShowScreensaver(league = 'mlb') {
  try {
    // Try to fetch screensaver data from dev server
    const response = await fetch(`/api/screensaver/${league}`);
    if (response.ok) {
      const data = await response.json();

      // Only show screensaver if we actually got article data (not empty response)
      if (data && data.title && data.image_url) {
        // Update header title based on the team
        const headerTitle = data.team ? `${data.team} News` : 'Team News';
        updateHeaderTitle(headerTitle);
        renderScreensaver(data);
        console.log(
          'Showed screensaver instead of no-games message:',
          data.title
        );
        return;
      }
    }

    // If screensaver fails or returns empty, fall back to no-games message
    showNoGamesMessage();
  } catch (error) {
    console.log('Screensaver not available, showing no-games message:', error);
    showNoGamesMessage();
  }
}

export function showNoGamesMessage() {
  const container = document.getElementById('games');
  const noGamesEl = document.createElement('div');
  noGamesEl.className = 'no-games-message';
  noGamesEl.textContent = 'There are no games scheduled for today';
  container.appendChild(noGamesEl);
  updateCurrentTime(''); // Empty string to hide the time text entirely
}
