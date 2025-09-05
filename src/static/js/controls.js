// UI controls and interaction logic
import {
  loadTestData,
  loadMLBData,
  loadMLBScheduledData,
  loadMLBEmptyData,
  loadNFLData,
  loadCFBData,
  fetchLiveData,
} from './data.js';
import { updateSizeIndicator, updateCurrentTime } from './renderer.js';

// Track target dimensions - make them globally accessible
export let targetWidth = 800;
export let targetHeight = 480;

// Also make them available on window for other files
window.targetWidth = targetWidth;
window.targetHeight = targetHeight;

// Dev tray toggle - make globally accessible for HTML onclick handlers
window.toggleDevTray = function toggleDevTray() {
  const controls = document.getElementById('devControls');
  const toggle = document.getElementById('devToggle');

  controls.classList.toggle('show');
  toggle.classList.toggle('expanded');
};

// Close tray when clicking outside
document.addEventListener('click', (e) => {
  const tray = document.querySelector('.dev-tray');
  if (!tray.contains(e.target)) {
    const controls = document.getElementById('devControls');
    const toggle = document.getElementById('devToggle');
    controls.classList.remove('show');
    toggle.classList.remove('expanded');
  }
});

// Resize functions - make globally accessible for HTML onclick handlers
window.setSize = function setSize(width, height) {
  const frame = document.getElementById('device-frame');
  const display = document.getElementById('display');
  frame.style.width = width + 40 + 'px'; // Add padding
  display.style.height = height + 'px';
  targetWidth = width;
  targetHeight = height;
  updateSizeIndicator();
};

// Make frame resizable with mouse
let isResizing = false;

// Initialize resizable functionality
function initResizable() {
  const frame = document.getElementById('device-frame');

  // Add resize handle
  const resizeHandle = document.createElement('div');
  resizeHandle.style.cssText =
    'position: absolute; bottom: 0; right: 0; width: 20px; height: 20px; cursor: nwse-resize; background: linear-gradient(135deg, transparent 50%, var(--color-gray-600) 50%);';
  frame.style.position = 'relative';
  frame.appendChild(resizeHandle);

  resizeHandle.addEventListener('mousedown', (e) => {
    isResizing = true;
    e.preventDefault();
  });

  document.addEventListener('mousemove', (e) => {
    if (!isResizing) return;
    const newWidth = e.clientX - frame.offsetLeft - 20;
    const newHeight = e.clientY - frame.offsetTop - 20;
    if (newWidth > 400 && newWidth < 1600) {
      frame.style.width = newWidth + 'px';
      targetWidth = newWidth - 40; // Subtract frame padding
    }
    if (newHeight > 300 && newHeight < 1300) {
      document.getElementById('display').style.height = newHeight - 40 + 'px';
      targetHeight = newHeight - 40; // Subtract frame padding
    }
    updateSizeIndicator();
  });

  document.addEventListener('mouseup', () => {
    isResizing = false;
  });
}

// Make data loading functions globally accessible for HTML onclick handlers
window.loadMLBData = loadMLBData;
window.loadMLBScheduledData = loadMLBScheduledData;
window.loadMLBEmptyData = loadMLBEmptyData;
window.loadNFLData = loadNFLData;
window.loadCFBData = loadCFBData;
window.fetchLiveData = fetchLiveData;

// Initialize the app
export async function initApp() {
  await loadTestData();
  loadMLBData();
  updateSizeIndicator();
  initResizable();

  // Update time every minute
  setInterval(updateCurrentTime, 60000);
}

// Initialize when page loads
initApp();
