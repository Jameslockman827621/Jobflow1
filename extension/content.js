// JobScale Content Script
// 1. Fetches jobs selected for auto-apply from user's dashboard
// 2. When user visits a matching job page, auto-applies for them

(function() {
  'use strict';

  const API_BASE = 'http://localhost:3000/api/v1';

  // Job data extractors for different sites
  const extractors = {
    'linkedin.com': () => {
      const title = document.querySelector('[data-test="job-title"]')?.textContent?.trim() ||
                    document.querySelector('.job-title')?.textContent?.trim();
      const company = document.querySelector('[data-test="company-name"]')?.textContent?.trim() ||
                      document.querySelector('.company-name')?.textContent?.trim();
      const location = document.querySelector('[data-test="text-primary"]')?.textContent?.trim() ||
                       document.querySelector('.job-location')?.textContent?.trim();
      return { title, company, location, source: 'linkedin' };
    },
    'indeed.com': () => {
      const title = document.querySelector('#jobTitle')?.textContent?.trim() ||
                    document.querySelector('h1.jobsearch-JobInfoHeader-title')?.textContent?.trim();
      const company = document.querySelector('[data-testid="company-name"]')?.textContent?.trim() ||
                      document.querySelector('.companyName')?.textContent?.trim();
      const location = document.querySelector('[data-testid="text-location"]')?.textContent?.trim();
      return { title, company, location, source: 'indeed' };
    },
    'glassdoor.com': () => {
      const title = document.querySelector('[data-test="jobTitle"]')?.textContent?.trim();
      const company = document.querySelector('[data-test="employerName"]')?.textContent?.trim();
      const location = document.querySelector('[data-test="location"]')?.textContent?.trim();
      return { title, company, location, source: 'glassdoor' };
    },
    'greenhouse.io': () => {
      const title = document.querySelector('h1')?.textContent?.trim();
      const company = document.querySelector('.company-name')?.textContent?.trim() ||
                      window.location.hostname.split('.')[0];
      const location = document.querySelector('.location')?.textContent?.trim();
      return { title, company, location, source: 'greenhouse' };
    },
    'lever.co': () => {
      const title = document.querySelector('h1')?.textContent?.trim();
      const company = document.querySelector('.company')?.textContent?.trim() ||
                      window.location.pathname.split('/')[2];
      const location = document.querySelector('.location')?.textContent?.trim();
      return { title, company, location, source: 'lever' };
    },
  };

  function getJobData() {
    const hostname = window.location.hostname;
    for (const [domain, extractor] of Object.entries(extractors)) {
      if (hostname.includes(domain)) {
        return extractor();
      }
    }
    return null;
  }

  function normalize(str) {
    if (!str || typeof str !== 'string') return '';
    return str.toLowerCase()
      .replace(/[^\w\s]/g, '')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function matches(pageJob, dashboardJob) {
    if (!pageJob?.title || !dashboardJob?.title) return false;
    const pageTitle = normalize(pageJob.title);
    const pageCompany = normalize(pageJob.company || '');
    const dashTitle = normalize(dashboardJob.title);
    const dashCompany = normalize(dashboardJob.company || '');
    const titleMatch = pageTitle.includes(dashTitle) || dashTitle.includes(pageTitle);
    const companyMatch = !dashCompany || pageCompany.includes(dashCompany) || dashCompany.includes(pageCompany);
    return titleMatch && companyMatch;
  }

  function showAutoApplyBanner(job, applied) {
    const existing = document.getElementById('jobscale-auto-apply-banner');
    if (existing) existing.remove();

    const banner = document.createElement('div');
    banner.id = 'jobscale-auto-apply-banner';
    banner.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      z-index: 99999;
      padding: 12px 20px;
      background: linear-gradient(135deg, #0d9488, #0f766e);
      color: white;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      font-size: 14px;
      text-align: center;
      box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    `;
    banner.textContent = applied
      ? `✓ Auto-applied to ${job.title} at ${job.company}! Check your new tab.`
      : `⏳ Auto-applying to ${job.title} at ${job.company}...`;
    document.body.prepend(banner);
    setTimeout(() => banner.remove(), 5000);
  }

  async function autoApply(matchingJob, pageJobData) {
    const { id: job_id } = matchingJob;
    const token = (await chrome.storage.local.get('jobscale_token')).jobscale_token;
    if (!token) {
      showAutoApplyBanner(pageJobData, false);
      return;
    }

    showAutoApplyBanner(pageJobData, false);

    try {
      const res = await fetch(`${API_BASE}/applications/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ job_id }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to start application');
      }

      const data = await res.json();
      if (data.job_url) {
        window.open(data.job_url, '_blank');
      }
      showAutoApplyBanner(pageJobData, true);
    } catch (err) {
      console.error('JobScale auto-apply error:', err);
      const banner = document.getElementById('jobscale-auto-apply-banner');
      if (banner) {
        banner.style.background = 'linear-gradient(135deg, #dc2626, #b91c1c)';
        banner.textContent = `Auto-apply failed: ${err.message}. Open dashboard to apply manually.`;
      }
    }
  }

  async function checkAndAutoApply() {
    const pageJob = getJobData();
    if (!pageJob?.title) return;

    const { jobscale_token } = await chrome.storage.local.get('jobscale_token');
    if (!jobscale_token) return;

    const res = await fetch(`${API_BASE}/auto-apply/jobs`, {
      headers: { 'Authorization': `Bearer ${jobscale_token}` },
    });
    if (!res.ok) return;

    const { jobs } = await res.json();
    if (!jobs?.length) return;

    const matching = jobs.find(j => matches(pageJob, j));
    if (matching) {
      const appliedKey = `jobscale_applied_${matching.id}_${window.location.href}`;
      const alreadyApplied = sessionStorage.getItem(appliedKey);
      if (!alreadyApplied) {
        sessionStorage.setItem(appliedKey, '1');
        await autoApply(matching, pageJob);
      }
    }
  }

  // Add floating button (for manual apply when not in auto-apply list)
  function addApplyButton() {
    const jobData = getJobData();
    if (!jobData?.title) return;

    const existing = document.getElementById('jobscale-apply-btn');
    if (existing) return;

    const button = document.createElement('button');
    button.id = 'jobscale-apply-btn';
    button.textContent = '🚀 Apply with JobScale';
    button.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      z-index: 9999;
      padding: 12px 24px;
      background: linear-gradient(135deg, #2563eb, #1d4ed8);
      color: white;
      border: none;
      border-radius: 8px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
      transition: all 0.2s;
    `;
    button.onmouseover = () => {
      button.style.transform = 'translateY(-2px)';
      button.style.boxShadow = '0 6px 16px rgba(37, 99, 235, 0.4)';
    };
    button.onmouseout = () => {
      button.style.transform = 'translateY(0)';
      button.style.boxShadow = '0 4px 12px rgba(37, 99, 235, 0.3)';
    };
    button.onclick = () => {
      window.open('http://localhost:3000/dashboard', '_blank');
    };
    document.body.appendChild(button);
  }

  // Listen for messages from popup
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'getJobData') {
      sendResponse(getJobData());
    }
  });

  // Run on page load
  setTimeout(() => {
    addApplyButton();
    checkAndAutoApply();
  }, 1500);

  // Re-check when URL changes (SPA navigation)
  let lastUrl = location.href;
  new MutationObserver(() => {
    if (location.href !== lastUrl) {
      lastUrl = location.href;
      setTimeout(() => {
        addApplyButton();
        checkAndAutoApply();
      }, 1000);
    }
  }).observe(document, { subtree: true, childList: true });
})();
