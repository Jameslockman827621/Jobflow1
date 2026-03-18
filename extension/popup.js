// JobScale Extension Popup
// User selects jobs in extension → clicks Apply → extension opens each URL and starts application

const API_BASE = 'http://localhost:3000/api/v1';

document.addEventListener('DOMContentLoaded', async () => {
  const loadingEl = document.getElementById('loading');
  const loggedOutEl = document.getElementById('logged-out');
  const loggedInEl = document.getElementById('logged-in');
  const jobsListEl = document.getElementById('jobs-list');
  const applyBtn = document.getElementById('apply-btn');
  const loginBtn = document.getElementById('login-btn');
  const dashboardBtn = document.getElementById('dashboard-btn');
  const userEmailEl = document.getElementById('user-email');
  const selectAllEl = document.getElementById('select-all');
  const statApplied = document.getElementById('stat-applied');
  const statInterviews = document.getElementById('stat-interviews');
  const statOffers = document.getElementById('stat-offers');

  loadingEl.style.display = 'flex';
  loggedOutEl.classList.add('hidden');
  loggedInEl.classList.add('hidden');

  const { jobscale_token } = await chrome.storage.local.get('jobscale_token');
  const token = jobscale_token;

  if (!token) {
    loadingEl.style.display = 'none';
    loggedOutEl.classList.remove('hidden');
  } else {
    try {
      const profileRes = await fetch(`${API_BASE}/profile/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!profileRes.ok) throw new Error('Not authenticated');

      const profile = await profileRes.json();
      userEmailEl.textContent = profile.first_name || profile.email || 'User';

      const appsRes = await fetch(`${API_BASE}/applications/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (appsRes.ok) {
        const data = await appsRes.json();
        const applications = data.applications || data;
        statApplied.textContent = applications.length;
        statInterviews.textContent = applications.filter(a => ['phone_screen', 'technical', 'onsite'].includes(a.stage)).length;
        statOffers.textContent = applications.filter(a => a.stage === 'offer' || a.status === 'offered').length;
      }

      loadingEl.style.display = 'none';
      loggedInEl.classList.remove('hidden');

      await loadJobs();
    } catch (error) {
      console.error('Error:', error);
      chrome.storage.local.remove('jobscale_token');
      loadingEl.style.display = 'none';
      loggedOutEl.classList.remove('hidden');
    }
  }

  async function loadJobs() {
    const headers = { Authorization: `Bearer ${token}` };
    const [jobsRes, autoApplyRes] = await Promise.all([
      fetch(`${API_BASE}/onboarding/jobs`, { headers }),
      fetch(`${API_BASE}/auto-apply/jobs`, { headers })
    ]);

    const jobs = jobsRes.ok ? (await jobsRes.json()).jobs || [] : [];
    const autoApplyJobs = autoApplyRes.ok ? (await autoApplyRes.json()).jobs || [] : [];
    const selectedIds = new Set(autoApplyJobs.map(j => j.id));

    if (jobs.length === 0) {
      jobsListEl.innerHTML = '<div class="empty-state">No jobs yet. Open dashboard and run a search first.</div>';
      return;
    }

    jobsListEl.innerHTML = jobs.map(job => `
      <div class="job-item" data-job-id="${job.id}">
        <input type="checkbox" id="job-${job.id}" ${selectedIds.has(job.id) ? 'checked' : ''}>
        <label for="job-${job.id}">
          <div class="title">${escapeHtml(job.title)}</div>
          <div class="company">${escapeHtml(job.company)}</div>
        </label>
      </div>
    `).join('');

    jobsListEl.querySelectorAll('.job-item').forEach(el => {
      const jobId = parseInt(el.dataset.jobId, 10);
      const checkbox = el.querySelector('input');
      checkbox.addEventListener('change', () => toggleAutoApply(jobId, checkbox.checked));
    });

    updateSelectAllText();
    selectAllEl.onclick = async () => {
      const allSelected = jobsListEl.querySelectorAll('input:checked').length === jobs.length;
      const newState = !allSelected;
      for (const el of jobsListEl.querySelectorAll('.job-item')) {
        const jobId = parseInt(el.dataset.jobId, 10);
        const checkbox = el.querySelector('input');
        checkbox.checked = newState;
        await toggleAutoApply(jobId, newState);
      }
      updateSelectAllText();
    };
  }

  function updateSelectAllText() {
    const total = jobsListEl.querySelectorAll('.job-item').length;
    const selected = jobsListEl.querySelectorAll('input:checked').length;
    selectAllEl.textContent = selected === total ? 'Deselect all' : 'Select all';
  }

  async function toggleAutoApply(jobId, add) {
    const method = add ? 'POST' : 'DELETE';
    await fetch(`${API_BASE}/auto-apply/jobs/${jobId}`, {
      method,
      headers: { Authorization: `Bearer ${token}` }
    });
    const total = jobsListEl.querySelectorAll('.job-item').length;
    const selected = jobsListEl.querySelectorAll('input:checked').length;
    selectAllEl.textContent = selected === total ? 'Deselect all' : 'Select all';
  }

  applyBtn.addEventListener('click', async () => {
    const { jobscale_token } = await chrome.storage.local.get('jobscale_token');
    if (!jobscale_token) return;

    const res = await fetch(`${API_BASE}/auto-apply/jobs`, {
      headers: { Authorization: `Bearer ${jobscale_token}` }
    });
    if (!res.ok) return;

    const { jobs } = await res.json();
    if (!jobs || jobs.length === 0) {
      alert('Select at least one job first (check the boxes above).');
      return;
    }

    applyBtn.disabled = true;
    applyBtn.textContent = `⏳ Opening ${jobs.length} job(s)...`;

    for (let i = 0; i < jobs.length; i++) {
      const job = jobs[i];
      try {
        const startRes = await fetch(`${API_BASE}/applications/start`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${jobscale_token}`
          },
          body: JSON.stringify({ job_id: job.id })
        });

        if (startRes.ok) {
          const data = await startRes.json();
          if (data.job_url) {
            chrome.tabs.create({ url: data.job_url });
          }
        }
        if (i < jobs.length - 1) {
          await new Promise(r => setTimeout(r, 500));
        }
      } catch (e) {
        console.error('Apply error:', e);
      }
    }

    applyBtn.disabled = false;
    applyBtn.textContent = '✨ Apply to Selected Jobs';
  });

  loginBtn.addEventListener('click', () => {
    chrome.tabs.create({ url: 'http://localhost:3000/login' });
  });

  dashboardBtn.addEventListener('click', () => {
    chrome.tabs.create({ url: 'http://localhost:3000/dashboard' });
  });
});

function escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
