// JobScale Background Service Worker

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

// Handle messages from content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'openDashboard') {
    chrome.tabs.create({ url: 'http://localhost:3000/dashboard' });
  }
});
