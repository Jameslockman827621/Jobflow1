/**
 * Runs on LinkedIn / Indeed — detects login and asks background to sync session.
 */
(function () {
  'use strict';

  function detectBoard() {
    const h = location.hostname.toLowerCase();
    if (h.includes('linkedin.com')) return 'linkedin';
    if (h.includes('indeed.com')) return 'indeed';
    return null;
  }

  function looksLoggedIn(board) {
    if (board === 'linkedin') {
      // Logged-in nav / feed; avoid login form
      if (document.querySelector('input#username, input[name="session_key"]')) return false;
      return !!(
        document.querySelector('img.global-nav__me-photo, .global-nav__me, [data-global-nav-link="profile"]')
        || document.body.innerText.toLowerCase().includes('me')
        || location.pathname.startsWith('/feed')
        || location.pathname.startsWith('/jobs')
      );
    }
    if (board === 'indeed') {
      if (document.querySelector('#login-email-input, form[action*="login"]')) {
        // Still might be logged in on other pages — check account menu
        if (!document.querySelector('[data-tn-element="user-account"], #AccountMenu, a[href*="account"]')) {
          return false;
        }
      }
      return true;
    }
    return false;
  }

  function toast(msg) {
    let el = document.getElementById('jobscale-connect-toast');
    if (!el) {
      el = document.createElement('div');
      el.id = 'jobscale-connect-toast';
      el.style.cssText =
        'position:fixed;bottom:24px;right:24px;z-index:2147483647;background:#0f172a;color:#fff;'
        + 'padding:12px 16px;border-radius:10px;font:13px/1.4 system-ui;max-width:300px;'
        + 'box-shadow:0 8px 24px rgba(0,0,0,.3)';
      document.body.appendChild(el);
    }
    el.textContent = msg;
    clearTimeout(el._t);
    el._t = setTimeout(() => el.remove(), 6000);
  }

  async function syncIfReady(force) {
    const board = detectBoard();
    if (!board) return;
    if (!force && !looksLoggedIn(board)) {
      toast('JobScale: log into ' + board + ' to connect Easy Apply');
      return;
    }
    try {
      chrome.runtime.sendMessage({ action: 'syncBoardSession', board }, (resp) => {
        if (chrome.runtime.lastError) return;
        if (resp && resp.ok) {
          toast('JobScale: ' + board + ' connected for Easy Apply');
        } else if (resp && resp.error) {
          toast('JobScale: ' + resp.error);
        }
      });
    } catch (e) { /* ignore */ }
  }

  // Auto-sync shortly after landing (user completed login)
  setTimeout(() => syncIfReady(false), 2500);

  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg && msg.action === 'requestBoardSync') {
      syncIfReady(true).then(() => sendResponse({ ok: true }));
      return true;
    }
  });

  window.JobScaleBoardConnect = { syncIfReady, detectBoard };
})();
