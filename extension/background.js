// JobScale Background Service Worker

const DASHBOARD_URL = 'http://localhost:3000';
const API_BASE = `${DASHBOARD_URL}/api/v1`;

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'apply-with-jobscale',
    title: 'Apply with JobScale',
    contexts: ['page', 'link'],
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'apply-with-jobscale') {
    chrome.tabs.create({ url: `${DASHBOARD_URL}/dashboard` });
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

  if (request.action === 'autoSession') {
    handleAutoSession(request.jobs, sendResponse);
    return true;
  }

  if (request.action === 'autoSessionStatus') {
    sendResponse({
      active: activeSession !== null,
      current: activeSession ? activeSession.currentIndex + 1 : 0,
      total: activeSession ? activeSession.jobs.length : 0,
      completed: activeSession ? activeSession.completed : 0,
      failed: activeSession ? activeSession.failed : 0,
    });
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

    const res = await fetch(`${API_BASE}/applications/ready-to-apply`, {
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


// ===== AUTONOMOUS APPLY SESSION =====
// When the user clicks "Start autonomous session" on the /apply page,
// the frontend sends a message to the extension with the list of jobs.
// The extension opens each job URL in a tab, waits for form_fill.js to
// fill + submit, receives the receipt, closes the tab, and moves to the next.

let activeSession = null;

async function handleAutoSession(jobs, sendResponse) {
  if (!jobs || jobs.length === 0) {
    sendResponse({ ok: false, error: 'No jobs to apply to' });
    return;
  }

  activeSession = {
    jobs: jobs,
    currentIndex: 0,
    completed: 0,
    failed: 0,
    tabId: null,
  };

  sendResponse({ ok: true, total: jobs.length, message: `Starting autonomous session with ${jobs.length} jobs` });

  // Process jobs one by one
  for (let i = 0; i < jobs.length; i++) {
    const job = jobs[i];
    activeSession.currentIndex = i;
    console.log(`[JobScale] Auto-session: processing ${i + 1}/${jobs.length} — ${job.job_title} at ${job.company}`);

    try {
      // Open the job application URL in a new tab
      const tab = await chrome.tabs.create({ url: job.external_url, active: false });
      activeSession.tabId = tab.id;

      // Wait for the content script to fill + submit + send receipt
      // The content script (form_fill.js) will auto-fill, auto-submit (if enabled),
      // and send a receipt. We wait up to 60 seconds for completion.
      const result = await waitForTabCompletion(tab.id, 60000);

      if (result.completed) {
        activeSession.completed++;
        console.log(`[JobScale] Auto-session: ✓ completed ${job.job_title} at ${job.company}`);
      } else {
        activeSession.failed++;
        console.log(`[JobScale] Auto-session: ✗ failed/timeout ${job.job_title} at ${job.company}`);
      }

      // Close the tab
      try {
        await chrome.tabs.remove(tab.id);
      } catch (e) {
        // Tab may already be closed
      }

      // Wait 3 seconds before the next job (rate limiting + politeness)
      if (i < jobs.length - 1) {
        await new Promise(r => setTimeout(r, 3000));
      }
    } catch (e) {
      console.error(`[JobScale] Auto-session: error processing job ${i}:`, e);
      activeSession.failed++;
    }
  }

  // Session complete
  console.log(`[JobScale] Auto-session complete: ${activeSession.completed} submitted, ${activeSession.failed} failed`);
  activeSession = null;
}

function waitForTabCompletion(tabId, timeoutMs) {
  return new Promise((resolve) => {
    let resolved = false;
    const timeout = setTimeout(() => {
      if (!resolved) {
        resolved = true;
        resolve({ completed: false, reason: 'timeout' });
      }
    }, timeoutMs);

    // Listen for a message from the content script indicating completion
    const listener = (request, sender, sendResponse) => {
      if (request.action === 'autoSubmitComplete' && sender.tab && sender.tab.id === tabId) {
        if (!resolved) {
          resolved = true;
          clearTimeout(timeout);
          chrome.runtime.onMessage.removeListener(listener);
          resolve({ completed: true, receipt: request.receipt });
        }
      }
    };
    chrome.runtime.onMessage.addListener(listener);

    // Also check if the tab was closed (form may have redirected after submit)
    chrome.tabs.onRemoved.addListener(function removedListener(closedTabId) {
      if (closedTabId === tabId && !resolved) {
        // Give it a moment in case the receipt message is in flight
        setTimeout(() => {
          if (!resolved) {
            resolved = true;
            clearTimeout(timeout);
            chrome.tabs.onRemoved.removeListener(removedListener);
            chrome.runtime.onMessage.removeListener(listener);
            resolve({ completed: true, reason: 'tab_closed_after_submit' });
          }
        }, 2000);
      }
    });
  });
}
