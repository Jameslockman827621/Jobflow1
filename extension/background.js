// JobScale Background Service Worker

const DASHBOARD_URL = 'http://localhost:3000';
const API_BASE = 'http://localhost:8000/api/v1';

const BOARD_URLS = {
  linkedin: 'https://www.linkedin.com/feed/',
  indeed: 'https://www.indeed.com/',
};

const COOKIE_URLS = {
  linkedin: ['https://www.linkedin.com', 'https://linkedin.com'],
  indeed: ['https://www.indeed.com', 'https://indeed.com'],
};

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'apply-with-jobscale',
    title: 'Apply with JobScale',
    contexts: ['page', 'link'],
  });
  chrome.contextMenus.create({
    id: 'connect-linkedin',
    title: 'Connect LinkedIn to JobScale',
    contexts: ['action'],
  });
  chrome.contextMenus.create({
    id: 'connect-indeed',
    title: 'Connect Indeed to JobScale',
    contexts: ['action'],
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'apply-with-jobscale') {
    chrome.tabs.create({ url: `${DASHBOARD_URL}/dashboard` });
  } else if (info.menuItemId === 'connect-linkedin') {
    startConnect('linkedin');
  } else if (info.menuItemId === 'connect-indeed') {
    startConnect('indeed');
  }
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'openDashboard') {
    chrome.tabs.create({ url: `${DASHBOARD_URL}/dashboard` });
  } else if (request.action === 'syncToken') {
    chrome.storage.local.set({ jobscale_token: request.token }, () => {
      sendResponse({ ok: true });
    });
    return true;
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

  if (request.action === 'applyFillComplete') {
    console.log('Apply fill complete', request);
    sendResponse({ ok: true });
  }

  if (request.action === 'syncBoardSession') {
    syncBoardSession(request.board)
      .then(sendResponse)
      .catch((e) => sendResponse({ ok: false, error: e.message }));
    return true;
  }

  if (request.action === 'connectBoard') {
    startConnect(request.board)
      .then(sendResponse)
      .catch((e) => sendResponse({ ok: false, error: e.message }));
    return true;
  }

  if (request.action === 'getConnectStatus') {
    getConnectStatus()
      .then(sendResponse)
      .catch((e) => sendResponse({ ok: false, error: e.message }));
    return true;
  }
});

async function getToken() {
  const data = await chrome.storage.local.get('jobscale_token');
  return data.jobscale_token || null;
}

async function collectCookies(board) {
  const urls = COOKIE_URLS[board] || [];
  const all = [];
  const seen = new Set();
  for (const url of urls) {
    const batch = await chrome.cookies.getAll({ url });
    for (const c of batch) {
      const key = `${c.domain}|${c.name}`;
      if (seen.has(key)) continue;
      seen.add(key);
      all.push({
        name: c.name,
        value: c.value,
        domain: c.domain,
        path: c.path,
        secure: c.secure,
        httpOnly: c.httpOnly,
        sameSite: c.sameSite,
        expirationDate: c.expirationDate,
      });
    }
  }
  // Also domain-wide fetch
  const domain = board === 'linkedin' ? '.linkedin.com' : '.indeed.com';
  try {
    const more = await chrome.cookies.getAll({ domain });
    for (const c of more) {
      const key = `${c.domain}|${c.name}`;
      if (seen.has(key)) continue;
      seen.add(key);
      all.push({
        name: c.name,
        value: c.value,
        domain: c.domain,
        path: c.path,
        secure: c.secure,
        httpOnly: c.httpOnly,
        sameSite: c.sameSite,
        expirationDate: c.expirationDate,
      });
    }
  } catch (e) { /* some Chrome builds restrict domain-only */ }
  return all;
}

async function syncBoardSession(board) {
  board = (board || '').toLowerCase();
  if (!['linkedin', 'indeed'].includes(board)) {
    return { ok: false, error: 'Unsupported board' };
  }
  const token = await getToken();
  if (!token) {
    return { ok: false, error: 'Sign in to JobScale dashboard first' };
  }
  const cookies = await collectCookies(board);
  if (!cookies.length) {
    return {
      ok: false,
      error: `No ${board} cookies yet — open ${board}.com and log in, then try again`,
    };
  }
  const res = await fetch(`${API_BASE}/apply-engine/board-sessions/${board}/from-cookies`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      cookies,
      label: `extension-${board}-${new Date().toISOString().slice(0, 10)}`,
    }),
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail || body);
    return { ok: false, error: detail || `HTTP ${res.status}`, status: res.status };
  }
  await chrome.storage.local.set({
    [`board_connected_${board}`]: true,
    [`board_connected_at_${board}`]: Date.now(),
  });
  return { ok: true, board, cookie_count: body.cookie_count, message: body.message };
}

async function startConnect(board) {
  board = (board || '').toLowerCase();
  const url = BOARD_URLS[board];
  if (!url) return { ok: false, error: 'Unsupported board' };

  // Open board so user can log in; then sync after a short delay + on tab complete
  const tab = await chrome.tabs.create({ url, active: true });
  // Attempt sync a few times while they log in
  const attempts = [4000, 10000, 20000];
  let last = { ok: false, error: 'Waiting for login…' };
  for (const wait of attempts) {
    await new Promise((r) => setTimeout(r, wait));
    last = await syncBoardSession(board);
    if (last.ok) {
      // Notify dashboard tabs
      const dashTabs = await chrome.tabs.query({ url: `${DASHBOARD_URL}/*` });
      for (const t of dashTabs) {
        try {
          chrome.tabs.sendMessage(t.id, { action: 'boardConnected', board });
        } catch (e) { /* ignore */ }
      }
      return last;
    }
  }
  // Ask content script on that tab to force sync
  if (tab && tab.id) {
    try {
      await chrome.tabs.sendMessage(tab.id, { action: 'requestBoardSync' });
      last = await syncBoardSession(board);
    } catch (e) { /* content script may not be ready */ }
  }
  return last;
}

async function getConnectStatus() {
  const token = await getToken();
  if (!token) return { ok: false, error: 'not_authenticated' };
  const res = await fetch(`${API_BASE}/apply-engine/connect/status`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) return { ok: false, error: `HTTP ${res.status}` };
  const body = await res.json();
  return { ok: true, ...body };
}

async function handleAutoApply(sendResponse) {
  try {
    const token = await getToken();
    if (!token) {
      sendResponse({ error: 'Not authenticated' });
      return;
    }

    const res = await fetch(`${API_BASE}/applications/ready-to-apply`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!res.ok) {
      sendResponse({ error: 'Failed to fetch applications' });
      return;
    }

    const result = await res.json();
    const apps = result.applications || [];

    for (const app of apps) {
      if (app.job_url) {
        await chrome.storage.local.set({
          pending_application_id: app.application_id,
          auto_fill_on_open: true,
        });
        await chrome.tabs.create({ url: app.job_url, active: false });
        await new Promise((r) => setTimeout(r, 1800));
      }
    }

    sendResponse({ success: true, count: apps.length, applications: apps, autofill: true });
  } catch (err) {
    sendResponse({ error: err.message });
  }
}
