// JobScale Extension Popup
// Uses chrome.storage for token (synced from dashboard via dashboard-bridge.js)

const API_BASE = 'http://localhost:3000/api/v1';

document.addEventListener('DOMContentLoaded', async () => {
  const loadingEl = document.getElementById('loading');
  const loggedOutEl = document.getElementById('logged-out');
  const loggedInEl = document.getElementById('logged-in');
  const jobDetectedEl = document.getElementById('job-detected');
  const jobInfoEl = document.getElementById('job-info');
  const applyBtn = document.getElementById('apply-btn');
  const loginBtn = document.getElementById('login-btn');
  const dashboardBtn = document.getElementById('dashboard-btn');
  const userEmailEl = document.getElementById('user-email');

  const statApplied = document.getElementById('stat-applied');
  const statInterviews = document.getElementById('stat-interviews');
  const statOffers = document.getElementById('stat-offers');

  loadingEl.style.display = 'flex';
  loggedOutEl.classList.add('hidden');
  loggedInEl.classList.add('hidden');

  // Get token from chrome.storage (synced from dashboard)
  const { jobscale_token } = await chrome.storage.local.get('jobscale_token');
  const token = jobscale_token;

  if (!token) {
    loadingEl.style.display = 'none';
    loggedOutEl.classList.remove('hidden');
  } else {
    try {
      const profileRes = await fetch(`${API_BASE}/profile/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!profileRes.ok) {
        throw new Error('Not authenticated');
      }

      const profile = await profileRes.json();
      userEmailEl.textContent = profile.first_name || profile.email || 'User';

      const appsRes = await fetch(`${API_BASE}/applications/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (appsRes.ok) {
        const data = await appsRes.json();
        const applications = data.applications || data;
        statApplied.textContent = applications.length;
        statInterviews.textContent = applications.filter(a => a.stage === 'interviewing' || a.stage === 'phone_screen' || a.stage === 'technical' || a.stage === 'onsite').length;
        statOffers.textContent = applications.filter(a => a.status === 'offered' || a.stage === 'offer').length;
      }

      loadingEl.style.display = 'none';
      loggedInEl.classList.remove('hidden');

      // Check if we're on a job page
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      let jobData = null;
      try {
        jobData = await chrome.tabs.sendMessage(tab.id, { action: 'getJobData' });
      } catch (e) {
        // Tab might not have content script (e.g. not a job board)
      }

      if (jobData && jobData.title) {
        jobDetectedEl.classList.remove('hidden');
        jobInfoEl.textContent = `${jobData.title} at ${jobData.company}`;
        applyBtn.classList.remove('hidden');
        chrome.storage.local.set({ currentJob: jobData });
      }
    } catch (error) {
      console.error('Error:', error);
      chrome.storage.local.remove('jobscale_token');
      loadingEl.style.display = 'none';
      loggedOutEl.classList.remove('hidden');
    }
  }

  loginBtn.addEventListener('click', () => {
    chrome.tabs.create({ url: 'http://localhost:3000/login' });
  });

  dashboardBtn.addEventListener('click', () => {
    chrome.tabs.create({ url: 'http://localhost:3000/dashboard' });
  });

  applyBtn.addEventListener('click', async () => {
    const { jobscale_token } = await chrome.storage.local.get('jobscale_token');
    if (!jobscale_token) return;

    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    let jobData = null;
    try {
      jobData = await chrome.tabs.sendMessage(tab.id, { action: 'getJobData' });
    } catch (e) {}

    if (!jobData) {
      alert('No job detected on this page. Select jobs in your dashboard for auto-apply.');
      chrome.tabs.create({ url: 'http://localhost:3000/dashboard' });
      return;
    }

    applyBtn.disabled = true;
    applyBtn.textContent = '⏳ Opening dashboard...';
    chrome.tabs.create({
      url: `http://localhost:3000/dashboard?apply=${encodeURIComponent(JSON.stringify(jobData))}`
    });
    applyBtn.disabled = false;
    applyBtn.textContent = '✨ Apply with AI';
  });
});
