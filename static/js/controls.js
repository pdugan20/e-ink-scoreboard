// UI controls and interaction logic

// Track target dimensions
let targetWidth = 800;
let targetHeight = 400;

// Dev tray toggle
function toggleDevTray() {
  const controls = document.getElementById('devControls');
  const toggle = document.getElementById('devToggle');

  controls.classList.toggle('show');
  toggle.classList.toggle('expanded');
}

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

// Resize functions
function setSize(width, height) {
  const frame = document.getElementById('device-frame');
  const display = document.getElementById('display');
  frame.style.width = width + 40 + 'px'; // Add padding
  display.style.height = height + 'px';
  targetWidth = width;
  targetHeight = height;
  updateSizeIndicator();
}

// Make frame resizable with mouse
let isResizing = false;

// Initialize resizable functionality
function initResizable() {
  const frame = document.getElementById('device-frame');

  // Add resize handle
  const resizeHandle = document.createElement('div');
  resizeHandle.style.cssText =
    'position: absolute; bottom: 0; right: 0; width: 20px; height: 20px; cursor: nwse-resize; background: linear-gradient(135deg, transparent 50%, #666 50%);';
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

// Initialize the app
async function initApp() {
  await loadTestData();
  loadMLBData();
  updateSizeIndicator();
  initResizable();

  // Update time every minute
  setInterval(updateCurrentTime, 60000);
}

// Initialize when page loads
initApp();

// Auto-refresh every 30 seconds
setInterval(() => {
  console.log('Auto-refreshing...');
  // fetchLiveData();
}, 30000);
