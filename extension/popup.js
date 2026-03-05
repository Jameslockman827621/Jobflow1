// JobScale Extension Popup

const API_URL = 'http://localhost:8000/api/v1';

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
  
  // Stats
  const statApplied = document.getElementById('stat-applied');
  const statInterviews = document.getElementById('stat-interviews');
  const statOffers = document.getElementById('stat-offers');
  
  loadingEl.style.display = 'flex';
  loggedOutEl.classList.add('hidden');
  loggedInEl.classList.add('hidden');
  
  // Check if user is logged in
  const token = localStorage.getItem('jobscale_token');
  
  if (!token) {
    loadingEl.style.display = 'none';
    loggedOutEl.classList.remove('hidden');
  } else {
    try {
      // Fetch user profile
      const profileRes = await fetch(`${API_URL}/profile/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!profileRes.ok) {
        throw new Error('Not authenticated');
      }
      
      const profile = await profileRes.json();
      userEmailEl.textContent = profile.first_name || profile.email || 'User';
      
      // Fetch applications count
      const appsRes = await fetch(`${API_URL}/applications/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (appsRes.ok) {
        const applications = await appsRes.json();
        statApplied.textContent = applications.length;
        statInterviews.textContent = applications.filter(a => a.stage === 'interviewing').length;
        statOffers.textContent = applications.filter(a => a.status === 'offered').length;
      }
      
      loadingEl.style.display = 'none';
      loggedInEl.classList.remove('hidden');
      
      // Check if we're on a job page
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      const jobData = await chrome.tabs.sendMessage(tab.id, { action: 'getJobData' });
      
      if (jobData && jobData.title) {
        jobDetectedEl.classList.remove('hidden');
        jobInfoEl.textContent = `${jobData.title} at ${jobData.company}`;
        applyBtn.classList.remove('hidden');
        
        // Store job data for application
        chrome.storage.local.set({ currentJob: jobData });
      }
      
    } catch (error) {
      console.error('Error:', error);
      localStorage.removeItem('jobscale_token');
      loadingEl.style.display = 'none';
      loggedOutEl.classList.remove('hidden');
    }
  }
  
  // Event listeners
  loginBtn.addEventListener('click', () => {
    chrome.tabs.create({ url: 'http://localhost:3000/login' });
  });
  
  dashboardBtn.addEventListener('click', () => {
    chrome.tabs.create({ url: 'http://localhost:3000/dashboard' });
  });
  
  applyBtn.addEventListener('click', async () => {
    const token = localStorage.getItem('jobscale_token');
    if (!token) return;
    
    // Get current job data
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const jobData = await chrome.tabs.sendMessage(tab.id, { action: 'getJobData' });
    
    if (!jobData) {
      alert('No job detected on this page');
      return;
    }
    
    applyBtn.disabled = true;
    applyBtn.textContent = '⏳ Applying...';
    
    try {
      // First, we need to save this job to our database
      // For now, open the dashboard to complete application
      chrome.tabs.create({ 
        url: `http://localhost:3000/dashboard?apply=${encodeURIComponent(JSON.stringify(jobData))}`
      });
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to start application');
    } finally {
      applyBtn.disabled = false;
      applyBtn.textContent = '✨ Apply with AI';
    }
  });
});
