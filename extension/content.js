// JobScale Content Script
// Detects job postings and enables auto-apply

(function() {
  'use strict';

  const extractors = {
    'linkedin.com': () => {
      const title = document.querySelector('[data-test="job-title"]')?.textContent?.trim() ||
                    document.querySelector('.job-title')?.textContent?.trim() ||
                    document.querySelector('h1.t-24')?.textContent?.trim();
      const company = document.querySelector('[data-test="company-name"]')?.textContent?.trim() ||
                      document.querySelector('.company-name')?.textContent?.trim() ||
                      document.querySelector('.jobs-unified-top-card__company-name')?.textContent?.trim();
      const location = document.querySelector('[data-test="text-primary"]')?.textContent?.trim() ||
                       document.querySelector('.job-location')?.textContent?.trim() ||
                       document.querySelector('.jobs-unified-top-card__bullet')?.textContent?.trim();
      return { title, company, location, source: 'linkedin', url: window.location.href };
    },

    'indeed.com': () => {
      const title = document.querySelector('#jobTitle')?.textContent?.trim() ||
                    document.querySelector('h1.jobsearch-JobInfoHeader-title')?.textContent?.trim();
      const company = document.querySelector('[data-testid="company-name"]')?.textContent?.trim() ||
                      document.querySelector('.companyName')?.textContent?.trim();
      const location = document.querySelector('[data-testid="text-location"]')?.textContent?.trim() ||
                       document.querySelector('.companyLocation')?.textContent?.trim();
      return { title, company, location, source: 'indeed', url: window.location.href };
    },

    'glassdoor.com': () => {
      const title = document.querySelector('[data-test="jobTitle"]')?.textContent?.trim();
      const company = document.querySelector('[data-test="employerName"]')?.textContent?.trim();
      const location = document.querySelector('[data-test="location"]')?.textContent?.trim();
      return { title, company, location, source: 'glassdoor', url: window.location.href };
    },

    'greenhouse.io': () => {
      const title = document.querySelector('h1')?.textContent?.trim();
      const company = document.querySelector('.company-name')?.textContent?.trim() || window.location.hostname.split('.')[0];
      const location = document.querySelector('.location')?.textContent?.trim();
      return { title, company, location, source: 'greenhouse', url: window.location.href };
    },

    'lever.co': () => {
      const title = document.querySelector('h1')?.textContent?.trim();
      const company = document.querySelector('.company')?.textContent?.trim() || window.location.pathname.split('/')[2];
      const location = document.querySelector('.location')?.textContent?.trim();
      return { title, company, location, source: 'lever', url: window.location.href };
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

  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'getJobData') {
      sendResponse(getJobData());
    }
  });

  function addApplyButton() {
    const jobData = getJobData();
    if (!jobData || !jobData.title) return;
    if (document.getElementById('jobscale-apply-btn')) return;

    const button = document.createElement('button');
    button.id = 'jobscale-apply-btn';
    button.innerHTML = '<span style="margin-right:6px">&#x1F680;</span> Apply with JobScale';
    button.style.cssText = `
      position: fixed; bottom: 20px; right: 20px; z-index: 9999;
      padding: 12px 24px; background: linear-gradient(135deg, #14b8a6, #0d9488);
      color: white; border: none; border-radius: 12px; font-size: 14px;
      font-weight: 600; cursor: pointer; box-shadow: 0 4px 12px rgba(20,184,166,0.3);
      transition: all 0.2s; font-family: -apple-system, system-ui, sans-serif;
    `;

    button.onmouseover = () => {
      button.style.transform = 'translateY(-2px)';
      button.style.boxShadow = '0 6px 16px rgba(20,184,166,0.4)';
    };
    button.onmouseout = () => {
      button.style.transform = 'translateY(0)';
      button.style.boxShadow = '0 4px 12px rgba(20,184,166,0.3)';
    };

    button.onclick = () => {
      chrome.runtime.sendMessage({
        action: 'openDashboard',
        jobData: jobData
      });
    };

    document.body.appendChild(button);
  }

  setTimeout(addApplyButton, 1500);
})();
