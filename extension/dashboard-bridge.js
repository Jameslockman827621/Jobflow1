// JobScale Dashboard Bridge
// Runs on the JobScale web app domain - syncs auth token to chrome.storage
// so the extension popup and content scripts can use it.
// Also syncs token CLEAR on logout so the extension doesn't hold a stale token.
(function() {
  'use strict';

  let lastToken = null;

  function syncToken() {
    try {
      const token = localStorage.getItem('jobscale_token');
      // Only send a message when the token actually changes
      if (token === lastToken) return;
      lastToken = token;

      if (token) {
        chrome.runtime.sendMessage({ action: 'syncToken', token: token }, () => {
          if (chrome.runtime.lastError) {
            // Extension context invalidated (extension reloaded) — reset so we retry
            lastToken = null;
          }
        });
      } else {
        // Token was removed (logout) — tell the extension to clear it too
        chrome.runtime.sendMessage({ action: 'clearToken' }, () => {
          if (chrome.runtime.lastError) {
            lastToken = null;
          }
        });
      }
    } catch (e) {
      // Cross-origin or extension not loaded
    }
  }

  // Sync on load
  syncToken();

  // Sync when storage changes (e.g. after login/logout in another tab)
  window.addEventListener('storage', (e) => {
    if (e.key === 'jobscale_token') {
      syncToken();
    }
  });

  // Poll for token changes (same-tab login/logout — storage event doesn't fire same-tab)
  setInterval(syncToken, 2000);
})();