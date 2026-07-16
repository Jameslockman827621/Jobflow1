// JobScale Content Script
// Floating controls + multi-step ATS form filling

(function () {
  'use strict';

  function addDashboardButton() {
    if (document.getElementById('jobscale-dashboard-btn')) return;

    const wrap = document.createElement('div');
    wrap.id = 'jobscale-dashboard-btn';
    wrap.style.cssText = 'position:fixed;bottom:20px;right:20px;z-index:99999;display:flex;flex-direction:column;gap:8px;';

    const fillBtn = document.createElement('button');
    fillBtn.textContent = 'Auto-fill form';
    fillBtn.title = 'Fill this application with your JobScale profile';
    fillBtn.style.cssText = btnStyle('#0f172a');
    fillBtn.onclick = async () => {
      fillBtn.disabled = true;
      fillBtn.textContent = 'Filling…';
      try {
        const { pending_application_id } = await chrome.storage.local.get('pending_application_id');
        if (window.JobScaleFormFiller) {
          await window.JobScaleFormFiller.autoFillFromJobScale(pending_application_id);
        } else {
          alert('Form filler not loaded. Reload the page.');
        }
      } finally {
        fillBtn.disabled = false;
        fillBtn.textContent = 'Auto-fill form';
      }
    };

    const dashBtn = document.createElement('button');
    dashBtn.textContent = 'JobScale';
    dashBtn.title = 'Open JobScale dashboard';
    dashBtn.style.cssText = btnStyle('#0d9488');
    dashBtn.onclick = async () => {
      let dash = 'http://localhost:3000';
      try {
        const data = await chrome.storage.local.get('dashboard_url');
        dash = (data.dashboard_url || dash).replace(/\/$/, '');
      } catch (e) { /* use default */ }
      window.open(`${dash}/dashboard`, '_blank');
    };

    wrap.appendChild(fillBtn);
    wrap.appendChild(dashBtn);
    document.body.appendChild(wrap);
  }

  function btnStyle(bg) {
    return `
      padding: 10px 16px;
      background: ${bg};
      color: white;
      border: none;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(15, 23, 42, 0.25);
      font-family: ui-sans-serif, system-ui, sans-serif;
    `;
  }

  // Auto-run when background opens a ready-to-apply tab
  async function maybeAutofill() {
    try {
      const data = await chrome.storage.local.get(['pending_application_id', 'auto_fill_on_open']);
      if (!data.auto_fill_on_open || !data.pending_application_id) return;
      if (!window.JobScaleFormFiller) return;
      await sleep(1800);
      await window.JobScaleFormFiller.autoFillFromJobScale(data.pending_application_id);
      await chrome.storage.local.set({ auto_fill_on_open: false });
    } catch (e) {
      console.warn('JobScale autofill skipped', e);
    }
  }

  function sleep(ms) {
    return new Promise(r => setTimeout(r, ms));
  }

  setTimeout(addDashboardButton, 1200);
  setTimeout(maybeAutofill, 2000);
})();
