// JobScale Content Script
// Detects job postings on various job boards

(function() {
  'use strict';
  
  // Job data extractor for different sites
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
  
  // Detect current site and extract job data
  function getJobData() {
    const hostname = window.location.hostname;
    
    for (const [domain, extractor] of Object.entries(extractors)) {
      if (hostname.includes(domain)) {
        return extractor();
      }
    }
    
    return null;
  }
  
  // Listen for messages from popup
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'getJobData') {
      const jobData = getJobData();
      sendResponse(jobData);
    }
  });
  
  // Add JobScale button to job pages
  function addApplyButton() {
    const jobData = getJobData();
    if (!jobData || !jobData.title) return;
    
    // Create floating button
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
      // Open extension popup or dashboard
      window.open('http://localhost:3000/dashboard', '_blank');
    };
    
    document.body.appendChild(button);
  }
  
  // Run on page load
  setTimeout(addApplyButton, 1000);
  
})();
