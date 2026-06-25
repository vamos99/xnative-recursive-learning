// Popup script to handle enabling or disabling capture.
const toggle = document.getElementById('captureToggle');
const statusEl = document.getElementById('status');

// Load saved state
chrome.storage.sync.get('captureEnabled', result => {
  const enabled = result.captureEnabled !== false; // treat undefined as true
  toggle.checked = enabled;
  statusEl.textContent = enabled ? 'Capture is enabled' : 'Capture is disabled';
});

toggle.addEventListener('change', () => {
  const enabled = toggle.checked;
  chrome.storage.sync.set({ captureEnabled: enabled }, () => {
    statusEl.textContent = enabled ? 'Capture is enabled' : 'Capture is disabled';
  });
});