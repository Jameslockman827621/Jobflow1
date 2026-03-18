// JobScale Content Script
// Shows floating button to open dashboard (main flow is via extension popup)

(function() {
  'use strict';

  function addDashboardButton() {
    if (document.getElementById('jobscale-dashboard-btn')) return;

    const button = document.createElement('button');
    button.id = 'jobscale-dashboard-btn';
    button.textContent = '🚀 JobScale';
    button.title = 'Open JobScale to select and apply to jobs';
    button.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      z-index: 9999;
      padding: 10px 20px;
      background: linear-gradient(135deg, #2563eb, #1d4ed8);
      color: white;
      border: none;
      border-radius: 8px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    `;
    button.onclick = () => window.open('http://localhost:3000/dashboard', '_blank');
    document.body.appendChild(button);
  }

  setTimeout(addDashboardButton, 1500);
})();
