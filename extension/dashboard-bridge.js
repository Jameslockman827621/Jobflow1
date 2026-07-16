// JobScale Dashboard Bridge
// Syncs auth token + handles Connect LinkedIn/Indeed from the dashboard page
(function () {
  'use strict';

  function syncToken() {
    try {
      const token = localStorage.getItem('jobscale_token');
      if (token) {
        chrome.runtime.sendMessage({ action: 'syncToken', token }, () => {});
      }
    } catch (e) {
      // Extension not loaded
    }
  }

  syncToken();

  window.addEventListener('storage', (e) => {
    if (e.key === 'jobscale_token' && e.newValue) {
      chrome.runtime.sendMessage({ action: 'syncToken', token: e.newValue }, () => {});
    }
  });

  setInterval(syncToken, 2000);

  // Dashboard → extension: Connect board
  window.addEventListener('jobscale-connect-board', (ev) => {
    const board = ev.detail && ev.detail.board;
    if (!board) return;
    syncToken();
    chrome.runtime.sendMessage({ action: 'connectBoard', board }, (resp) => {
      window.dispatchEvent(
        new CustomEvent('jobscale-connect-result', {
          detail: resp || { ok: false, error: 'Extension did not respond — is it installed?' },
        })
      );
    });
  });

  // Dashboard asks for status
  window.addEventListener('jobscale-connect-status', () => {
    chrome.runtime.sendMessage({ action: 'getConnectStatus' }, (resp) => {
      window.dispatchEvent(
        new CustomEvent('jobscale-connect-status-result', { detail: resp || { ok: false } })
      );
    });
  });

  // Background → page when connect succeeds
  try {
    chrome.runtime.onMessage.addListener((msg) => {
      if (msg && msg.action === 'boardConnected') {
        window.dispatchEvent(
          new CustomEvent('jobscale-board-connected', { detail: { board: msg.board } })
        );
      }
    });
  } catch (e) { /* ignore */ }

  // Expose for React without custom events if needed
  window.JobScaleExtension = {
    connectBoard(board) {
      return new Promise((resolve) => {
        window.dispatchEvent(new CustomEvent('jobscale-connect-board', { detail: { board } }));
        const handler = (ev) => {
          window.removeEventListener('jobscale-connect-result', handler);
          resolve(ev.detail);
        };
        window.addEventListener('jobscale-connect-result', handler);
        setTimeout(() => resolve({ ok: false, error: 'timeout' }), 45000);
      });
    },
    installed: true,
  };
})();
