// JobScale Background Service Worker

const API_URL = 'http://localhost:8000/api/v1';

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'apply-with-jobscale',
    title: 'Apply with JobScale',
    contexts: ['page', 'link'],
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'apply-with-jobscale') {
    chrome.tabs.create({ url: 'http://localhost:3000/dashboard' });
  }
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'openDashboard') {
    chrome.tabs.create({ url: 'http://localhost:3000/dashboard' });
  }

  if (request.action === 'setToken') {
    chrome.storage.local.set({ jobscale_token: request.token });
    sendResponse({ ok: true });
  }

  if (request.action === 'getToken') {
    chrome.storage.local.get('jobscale_token', (data) => {
      sendResponse({ token: data.jobscale_token || null });
    });
    return true;
  }

  if (request.action === 'clearToken') {
    chrome.storage.local.remove('jobscale_token');
    sendResponse({ ok: true });
  }

  if (request.action === 'autoApply') {
    handleAutoApply(sendResponse);
    return true;
  }
});

async function handleAutoApply(sendResponse) {
  try {
    const data = await chrome.storage.local.get('jobscale_token');
    const token = data.jobscale_token;
    if (!token) {
      sendResponse({ error: 'Not authenticated' });
      return;
    }

    const res = await fetch(`${API_URL}/applications/ready-to-apply`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!res.ok) {
      sendResponse({ error: 'Failed to fetch applications' });
      return;
    }

    const result = await res.json();
    const apps = result.applications || [];

    for (const app of apps) {
      if (app.job_url) {
        await chrome.tabs.create({ url: app.job_url, active: false });
        await new Promise(r => setTimeout(r, 1500));
      }
    }

    sendResponse({ success: true, count: apps.length, applications: apps });
  } catch (err) {
    sendResponse({ error: err.message });
  }
}
