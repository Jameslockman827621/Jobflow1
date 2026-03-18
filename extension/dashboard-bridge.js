// JobScale Dashboard Bridge
// Runs on localhost:3000 - syncs auth token to chrome.storage so the extension can use it
(function() {
  'use strict';

  function syncToken() {
    try {
      const token = localStorage.getItem('jobscale_token');
      if (token) {
        chrome.runtime.sendMessage({ action: 'syncToken', token: token }, () => {});
      }
    } catch (e) {
      // Cross-origin or extension not loaded
    }
  }

  // Sync on load
  syncToken();

  // Sync when storage changes (e.g. after login in another tab)
  window.addEventListener('storage', (e) => {
    if (e.key === 'jobscale_token' && e.newValue) {
      chrome.runtime.sendMessage({ action: 'syncToken', token: e.newValue }, () => {});
    }
  });

  // Poll for token changes (same-tab login)
  setInterval(syncToken, 2000);
})();
