// JobScale Extension Popup

const API_URL = 'http://localhost:8000/api/v1';

document.addEventListener('DOMContentLoaded', async () => {
  const loadingEl = document.getElementById('loading');
  const loggedOutEl = document.getElementById('logged-out');
  const loggedInEl = document.getElementById('logged-in');
  const jobDetectedEl = document.getElementById('job-detected');
  const jobInfoEl = document.getElementById('job-info');
  const applyBtn = document.getElementById('apply-btn');
  const autoApplyBtn = document.getElementById('auto-apply-btn');
  const loginBtn = document.getElementById('login-btn');
  const dashboardBtn = document.getElementById('dashboard-btn');
  const userEmailEl = document.getElementById('user-email');
  const statApplied = document.getElementById('stat-applied');
  const statInterviews = document.getElementById('stat-interviews');
  const statOffers = document.getElementById('stat-offers');
  const readyCountEl = document.getElementById('ready-count');
  const readySectionEl = document.getElementById('ready-section');

  loadingEl.style.display = 'flex';
  loggedOutEl.classList.add('hidden');
  loggedInEl.classList.add('hidden');

  let token = null;
  try {
    const data = await chrome.storage.local.get('jobscale_token');
    token = data.jobscale_token;
  } catch (e) {
    console.error('Storage error:', e);
  }

  if (!token) {
    loadingEl.style.display = 'none';
    loggedOutEl.classList.remove('hidden');
  } else {
    try {
      const profileRes = await fetch(`${API_URL}/profile/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!profileRes.ok) throw new Error('Not authenticated');

      const profile = await profileRes.json();
      userEmailEl.textContent = profile.first_name || profile.email || 'User';

      const appsRes = await fetch(`${API_URL}/applications/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (appsRes.ok) {
        const appsData = await appsRes.json();
        const applications = appsData.applications || [];
        statApplied.textContent = applications.filter(a => a.status === 'submitted' || a.status === 'ready_to_apply').length;
        statInterviews.textContent = applications.filter(a => a.stage === 'phone_screen' || a.stage === 'technical' || a.stage === 'onsite').length;
        statOffers.textContent = applications.filter(a => a.stage === 'offer').length;
      }

      const readyRes = await fetch(`${API_URL}/applications/ready-to-apply`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (readyRes.ok) {
        const readyData = await readyRes.json();
        const readyApps = readyData.applications || [];
        if (readyApps.length > 0) {
          readySectionEl.classList.remove('hidden');
          readyCountEl.textContent = readyApps.length;
        }
      }

      loadingEl.style.display = 'none';
      loggedInEl.classList.remove('hidden');

      try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (tab && tab.id) {
          const jobData = await chrome.tabs.sendMessage(tab.id, { action: 'getJobData' });
          if (jobData && jobData.title) {
            jobDetectedEl.classList.remove('hidden');
            jobInfoEl.textContent = `${jobData.title} at ${jobData.company}`;
            applyBtn.classList.remove('hidden');
            chrome.storage.local.set({ currentJob: jobData });
          }
        }
      } catch (e) {
        // Content script not loaded on this page
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
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      const jobData = await chrome.tabs.sendMessage(tab.id, { action: 'getJobData' });
      if (!jobData) { alert('No job detected'); return; }
      chrome.tabs.create({
        url: `http://localhost:3000/dashboard?apply=${encodeURIComponent(JSON.stringify(jobData))}`
      });
    } catch (error) {
      alert('Failed to detect job on this page');
    }
  });

  if (autoApplyBtn) {
    autoApplyBtn.addEventListener('click', async () => {
      autoApplyBtn.disabled = true;
      autoApplyBtn.textContent = 'Opening job pages...';
      chrome.runtime.sendMessage({ action: 'autoApply' }, (response) => {
        if (response && response.success) {
          autoApplyBtn.textContent = `Opened ${response.count} job pages!`;
          setTimeout(() => {
            autoApplyBtn.disabled = false;
            autoApplyBtn.textContent = 'Auto-Apply to Selected Jobs';
          }, 3000);
        } else {
          autoApplyBtn.textContent = response?.error || 'Failed';
          autoApplyBtn.disabled = false;
        }
      });
    });
  }
});
