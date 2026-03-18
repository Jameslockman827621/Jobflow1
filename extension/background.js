// JobScale Background Service Worker

const API_BASE = 'http://localhost:3000/api/v1';

// Install context menu
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'apply-with-jobscale',
    title: 'Apply with JobScale 🚀',
    contexts: ['page', 'link'],
  });
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'apply-with-jobscale') {
    chrome.tabs.create({
      url: 'http://localhost:3000/dashboard'
    });
  }
});

// Handle messages from content scripts and dashboard bridge
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'openDashboard') {
    chrome.tabs.create({ url: 'http://localhost:3000/dashboard' });
  } else if (request.action === 'syncToken') {
    chrome.storage.local.set({ jobscale_token: request.token }, () => {
      sendResponse({ ok: true });
    });
    return true; // Async response
  }
});
