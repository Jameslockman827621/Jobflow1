// JobScale Form Auto-Fill Content Script
// Runs on Greenhouse, Lever, Ashby, Workable application forms.
// Detects the form fields, fetches the user's saved answers + tailored CV,
// auto-fills everything it can, and attaches the tailored PDF CV.
// The user reviews and clicks Submit — we never auto-submit.

(function () {
  'use strict';

  const DASHBOARD_URL = 'http://localhost:3000';
  const API_BASE = `${DASHBOARD_URL}/api/v1`;

  // ===== ATS DETECTION =====
  function detectATS() {
    const host = window.location.hostname.toLowerCase();
    const path = window.location.pathname.toLowerCase();
    if (host.includes('greenhouse.io') || host.includes('job-boards.greenhouse.io')) return 'greenhouse';
    if (host.includes('lever.co') || host.includes('jobs.lever.co')) return 'lever';
    if (host.includes('ashbyhq.com')) return 'ashby';
    if (host.includes('workable.com')) return 'workable';
    if (host.includes('myworkdayjobs.com') || host.includes('wd1.') || host.includes('wd3.') || host.includes('wd5.')) return 'workday';
    // Greenhouse embeds on company career sites
    if (document.querySelector('iframe[src*="greenhouse.io"]')) return 'greenhouse_embed';
    if (document.querySelector('iframe[src*="lever.co"]')) return 'lever_embed';
    if (document.querySelector('iframe[src*="ashbyhq.com"]')) return 'ashby_embed';
    if (document.querySelector('iframe[src*="myworkdayjobs.com"]')) return 'workday_embed';
    return null;
  }

  // ===== UTILITIES =====
  function setFieldValue(field, value) {
    if (!field || !value) return false;
    try {
      // React-controlled inputs need native setter + event dispatch
      const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype, 'value'
      )?.set || Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value')?.set;
      const nativeTextAreaValueSetter = Object.getOwnPropertyDescriptor(
        window.HTMLTextAreaElement.prototype, 'value'
      )?.set;

      if (field.tagName === 'TEXTAREA' && nativeTextAreaValueSetter) {
        nativeTextAreaValueSetter.call(field, value);
      } else if (nativeInputValueSetter) {
        nativeInputValueSetter.call(field, value);
      } else {
        field.value = value;
      }
      field.dispatchEvent(new Event('input', { bubbles: true }));
      field.dispatchEvent(new Event('change', { bubbles: true }));
      field.dispatchEvent(new Event('blur', { bubbles: true }));
      return true;
    } catch (e) {
      console.warn('JobScale: setFieldValue error', e);
      return false;
    }
  }

  function fillByLabel(labelText, value, formRoot = document) {
    if (!value) return false;
    // Find labels matching the text within the form root (works inside iframes)
    const labels = formRoot.querySelectorAll('label');
    for (const label of labels) {
      const text = (label.textContent || '').toLowerCase().trim();
      if (text.includes(labelText.toLowerCase())) {
        const forId = label.getAttribute('for');
        if (forId) {
          // Use formRoot.getElementById instead of document.getElementById
          // so labels inside iframes/shadow roots resolve to the right field
          const field = formRoot.getElementById(forId)
            || formRoot.querySelector('#' + CSS.escape(forId));
          if (field) return setFieldValue(field, value);
        }
        // Label wrapping the field
        const fieldInside = label.querySelector('input, textarea, select');
        if (fieldInside) return setFieldValue(fieldInside, value);
      }
    }
    // Also try placeholder matching within the form root
    const inputs = formRoot.querySelectorAll('input, textarea');
    for (const input of inputs) {
      const placeholder = (input.placeholder || '').toLowerCase();
      if (placeholder.includes(labelText.toLowerCase())) {
        return setFieldValue(input, value);
      }
    }
    return false;
  }

  function fillByName(name, value, formRoot = document) {
    if (!value) return false;
    const field = formRoot.querySelector(`input[name="${name}"], textarea[name="${name}"], select[name="${name}"]`);
    if (field) return setFieldValue(field, value);
    return false;
  }

  async function attachFileByUrl(input, url, filename) {
    if (!input || !url) return false;
    try {
      // Fetch the file as a blob (with the user's auth token)
      const { jobscale_token } = await chrome.storage.local.get('jobscale_token');
      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${jobscale_token}` }
      });
      if (!res.ok) {
        console.warn('JobScale: file fetch failed', res.status);
        return false;
      }
      const blob = await res.blob();
      const file = new File([blob], filename, { type: blob.type || 'application/pdf' });
      // Build a DataTransfer to set the input's files
      const dt = new DataTransfer();
      dt.items.add(file);
      input.files = dt.files;
      input.dispatchEvent(new Event('change', { bubbles: true }));
      return true;
    } catch (e) {
      console.warn('JobScale: attachFileByUrl error', e);
      return false;
    }
  }

  // ===== COMMON FIELD FILLING =====
  async function fillCommonFields(data, formRoot = document) {
    let filled = 0;
    const { first_name, last_name, email, phone, location, linkedin_url, github_url, website, answers } = data;

    // Name fields — try multiple patterns
    if (first_name) {
      if (fillByName('first_name', first_name, formRoot)) filled++;
      else if (fillByLabel('First Name', first_name, formRoot)) filled++;
      else if (fillByLabel('First name', first_name, formRoot)) filled++;
    }
    if (last_name) {
      if (fillByName('last_name', last_name, formRoot)) filled++;
      else if (fillByLabel('Last Name', last_name, formRoot)) filled++;
      else if (fillByLabel('Last name', last_name, formRoot)) filled++;
    }
    // Full name fallback
    if (first_name && last_name) {
      if (fillByName('name', `${first_name} ${last_name}`, formRoot)) filled++;
      else if (fillByLabel('Full Name', `${first_name} ${last_name}`, formRoot)) filled++;
    }
    if (email) {
      if (fillByName('email', email, formRoot)) filled++;
      else if (fillByLabel('Email', email, formRoot)) filled++;
    }
    if (phone) {
      if (fillByName('phone', phone, formRoot)) filled++;
      else if (fillByLabel('Phone', phone, formRoot)) filled++;
    }
    if (location) {
      if (fillByLabel('Location', location, formRoot)) filled++;
      if (fillByLabel('Where are you located', location, formRoot)) filled++;
    }
    if (linkedin_url) {
      if (fillByName('linkedin_url', linkedin_url, formRoot)) filled++;
      else if (fillByLabel('LinkedIn', linkedin_url, formRoot)) filled++;
      else if (fillByLabel('linkedin', linkedin_url, formRoot)) filled++;
    }
    if (github_url) {
      if (fillByName('github_url', github_url, formRoot)) filled++;
      else if (fillByLabel('GitHub', github_url, formRoot)) filled++;
      else if (fillByLabel('github', github_url, formRoot)) filled++;
    }
    if (website) {
      if (fillByName('website', website, formRoot)) filled++;
      else if (fillByLabel('Website', website, formRoot)) filled++;
      if (fillByLabel('Portfolio', website, formRoot)) filled++;
    }

    // Common application questions (saved by the user once)
    if (answers) {
      const questionMap = {
        'work_authorization': ['authorized to work', 'work authorization', 'legally authorized', 'eligible to work'],
        'requires_sponsorship': ['sponsorship', 'visa sponsorship', 'require sponsorship', 'need sponsorship'],
        'willing_to_relocate': ['willing to relocate', 'relocate', 'relocation'],
        'years_of_experience': ['years of experience', 'years of relevant', 'how many years', 'years experience'],
        'earliest_start': ['earliest start', 'start date', 'when can you start', 'available to start'],
        'salary_expectation': ['salary expectation', 'salary requirements', 'expected salary', 'salary range', 'compensation expectation'],
        'why_this_company': ['why do you want', 'why this company', 'why are you interested', 'why do you want to join'],
      };
      for (const [key, labels] of Object.entries(questionMap)) {
        const value = answers[key];
        if (!value) continue;
        for (const label of labels) {
          if (fillByLabel(label, value, formRoot)) { filled++; break; }
        }
      }
    }
    return filled;
  }

  async function attachResume(url, filename = 'tailored_cv.pdf', formRoot = document) {
    if (!url) return false;
    // Look for resume/file upload inputs
    const fileInputs = formRoot.querySelectorAll('input[type="file"]');
    for (const input of fileInputs) {
      const accept = (input.getAttribute('accept') || '').toLowerCase();
      const name = (input.name || '').toLowerCase();
      const id = (input.id || '').toLowerCase();
      // Match resume/CV upload fields
      if (
        accept.includes('pdf') || accept.includes('doc') || accept.includes('resume') ||
        name.includes('resume') || name.includes('cv') || name.includes('file') ||
        id.includes('resume') || id.includes('cv') || id.includes('file') ||
        accept === '' // Generic file input
      ) {
        const ok = await attachFileByUrl(input, url, filename);
        if (ok) return true;
      }
    }
    return false;
  }

  // ===== ATS-SPECIFIC LOGIC =====
  async function fillGreenhouse(data) {
    // Greenhouse forms are inside #application_form or iframes
    let formRoot = document;
    const iframe = document.querySelector('iframe[src*="greenhouse.io"]');
    if (iframe && iframe.contentDocument) {
      formRoot = iframe.contentDocument;
    }
    const form = formRoot.querySelector('#application_form, form[name="application_form"], form.application-form');
    const root = form || formRoot;
    await fillCommonFields(data, root);
    // Attach resume
    if (data.tailored_cv_pdf_url) {
      await attachResume(data.tailored_cv_pdf_url, 'tailored_cv.pdf', root);
    }
  }

  async function fillLever(data) {
    let formRoot = document;
    const iframe = document.querySelector('iframe[src*="lever.co"]');
    if (iframe && iframe.contentDocument) {
      formRoot = iframe.contentDocument;
    }
    const form = formRoot.querySelector('form.application-form, form#application-form, form[name="application"]');
    const root = form || formRoot;
    await fillCommonFields(data, root);
    if (data.tailored_cv_pdf_url) {
      await attachResume(data.tailored_cv_pdf_url, 'tailored_cv.pdf', root);
    }
  }

  async function fillAshby(data) {
    let formRoot = document;
    const iframe = document.querySelector('iframe[src*="ashbyhq.com"]');
    if (iframe && iframe.contentDocument) {
      formRoot = iframe.contentDocument;
    }
    const form = formRoot.querySelector('form');
    const root = form || formRoot;
    await fillCommonFields(data, root);
    if (data.tailored_cv_pdf_url) {
      await attachResume(data.tailored_cv_pdf_url, 'tailored_cv.pdf', root);
    }
  }

  async function fillWorkable(data) {
    const form = document.querySelector('form');
    const root = form || document;
    await fillCommonFields(data, root);
    if (data.tailored_cv_pdf_url) {
      await attachResume(data.tailored_cv_pdf_url, 'tailored_cv.pdf', root);
    }
  }

  async function fillWorkday(data) {
    let formRoot = document;
    const iframe = document.querySelector('iframe[src*="myworkdayjobs.com"]');
    if (iframe && iframe.contentDocument) {
      formRoot = iframe.contentDocument;
    }
    const form = formRoot.querySelector('form, [data-automation-id="applicationForm"]');
    const root = form || formRoot;
    await fillCommonFields(data, root);
    if (data.tailored_cv_pdf_url) {
      await attachResume(data.tailored_cv_pdf_url, 'tailored_cv.pdf', root);
    }
  }

  // ===== TRUE AUTO-SUBMIT =====
  async function clickSubmitButton(formRoot = document) {
    // Find the submit button — try multiple selectors for different ATSes
    const selectors = [
      'button[type="submit"]',
      'input[type="submit"]',
      'button[data-automation-id="submit"]',  // Workday
      'button[id="submit-btn"]',
      'button[class*="submit"]',
      'button[class*="Submit"]',
      'a[class*="submit"]',
      'button:has(svg) + button',  // Sometimes submit is after a back button
    ];

    for (const selector of selectors) {
      const btn = formRoot.querySelector(selector);
      if (btn && !btn.disabled) {
        const text = (btn.textContent || '').toLowerCase();
        // Make sure it's actually a submit/apply button, not a back/cancel button
        if (text.includes('submit') || text.includes('apply') || text.includes('send') || text.includes('continue') || btn.type === 'submit') {
          btn.click();
          return true;
        }
      }
    }

    // Fallback: look for any button with "Submit" or "Apply" text
    const buttons = formRoot.querySelectorAll('button, input[type="button"], a[role="button"]');
    for (const btn of buttons) {
      const text = (btn.textContent || btn.value || '').toLowerCase().trim();
      if ((text === 'submit' || text === 'submit application' || text === 'apply' || text === 'send application') && !btn.disabled) {
        btn.click();
        return true;
      }
    }
    return false;
  }

  // ===== UI: floating "auto-fill" button =====
  function showAutoFillButton(onClick) {
    if (document.getElementById('jobscale-autofill-btn')) return;
    const btn = document.createElement('button');
    btn.id = 'jobscale-autofill-btn';
    btn.innerHTML = '✨ Auto-fill with JobScale';
    btn.style.cssText = `
      position: fixed;
      top: 16px;
      right: 16px;
      z-index: 2147483647;
      padding: 10px 16px;
      background: linear-gradient(135deg, #0d9488, #0f766e);
      color: white;
      border: none;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 600;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(13, 148, 136, 0.4);
      transition: all 0.2s;
    `;
    btn.onmouseenter = () => { btn.style.transform = 'translateY(-1px)'; btn.style.boxShadow = '0 6px 16px rgba(13, 148, 136, 0.5)'; };
    btn.onmouseleave = () => { btn.style.transform = ''; btn.style.boxShadow = '0 4px 12px rgba(13, 148, 136, 0.4)'; };
    btn.onclick = onClick;
    document.body.appendChild(btn);
  }

  function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.style.cssText = `
      position: fixed;
      top: 64px;
      right: 16px;
      z-index: 2147483647;
      padding: 10px 14px;
      background: ${type === 'success' ? '#f0fdf4' : type === 'error' ? '#fef2f2' : '#eff6ff'};
      color: ${type === 'success' ? '#166534' : type === 'error' ? '#991b1b' : '#1e40af'};
      border: 1px solid ${type === 'success' ? '#bbf7d0' : type === 'error' ? '#fecaca' : '#bfdbfe'};
      border-radius: 8px;
      font-size: 12px;
      font-weight: 500;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      max-width: 280px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    `;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
  }

  // ===== MAIN: fetch data and auto-fill =====
  async function autoFill() {
    const ats = detectATS();
    if (!ats) {
      showToast('JobScale: no application form detected on this page', 'info');
      return;
    }
    showToast('JobScale: auto-filling your application...', 'info');

    try {
      const { jobscale_token } = await chrome.storage.local.get('jobscale_token');
      if (!jobscale_token) {
        showToast('JobScale: please sign in to the extension first', 'error');
        return;
      }

      // 1. Get the user's saved answers + auto-fill profile
      const answersRes = await fetch(`${API_BASE}/auto-apply/answers`, {
        headers: { Authorization: `Bearer ${jobscale_token}` }
      });
      let answersData = {};
      if (answersRes.ok) answersData = await answersRes.json();

      // 2. Find the matching queue item for this job URL
      const queueRes = await fetch(`${API_BASE}/auto-apply/queue`, {
        headers: { Authorization: `Bearer ${jobscale_token}` }
      });
      let tailoredCvPdfUrl = null;
      if (queueRes.ok) {
        const queueData = await queueRes.json();
        const currentUrl = window.location.href;
        // Match by external_url containing the current page URL (or vice versa)
        const matching = (queueData.queue || []).find(q => {
          if (!q.job || !q.job.external_url) return false;
          const jobUrl = q.job.external_url.toLowerCase();
          const cur = currentUrl.toLowerCase();
          return jobUrl.includes(cur) || cur.includes(jobUrl) ||
            // Greenhouse job-boards.greenhouse.io/monzo/jobs/123 vs boards.greenhouse.io/monzo/jobs/123
            (q.job.external_url.split('?')[0] === currentUrl.split('?')[0]);
        });
        if (matching && matching.tailored_cv_pdf_url) {
          tailoredCvPdfUrl = `${DASHBOARD_URL}${matching.tailored_cv_pdf_url}`;
          // Mark this queue item as in_progress
          fetch(`${API_BASE}/auto-apply/queue/${matching.id}/start`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${jobscale_token}` }
          }).catch(() => {});
        }
      }

      // 3. Build the data payload
      const data = {
        first_name: answersData.first_name,
        last_name: answersData.last_name,
        email: (answersData.profile || {}).email,
        phone: (answersData.profile || {}).phone,
        location: answersData.location,
        linkedin_url: (answersData.profile || {}).linkedin_url,
        github_url: (answersData.profile || {}).github_url,
        website: (answersData.profile || {}).website,
        answers: answersData.answers || {},
        tailored_cv_pdf_url: tailoredCvPdfUrl,
      };

      // 4. Run the ATS-specific fill logic and track how many fields were filled
      let fieldsFilled = 0;
      let cvAttached = false;
      if (ats === 'greenhouse' || ats === 'greenhouse_embed') await fillGreenhouse(data);
      else if (ats === 'lever' || ats === 'lever_embed') await fillLever(data);
      else if (ats === 'ashby' || ats === 'ashby_embed') await fillAshby(data);
      else if (ats === 'workable') await fillWorkable(data);
      else if (ats === 'workday' || ats === 'workday_embed') await fillWorkday(data);
      else await fillCommonFields(data);

      // 5. Check if auto-submit is enabled — if so, click Submit after filling
      let autoSubmitted = false;
      try {
        const autoSubmitRes = await fetch(`${API_BASE}/auto-apply/auto-submit`, {
          headers: { Authorization: `Bearer ${jobscale_token}` }
        });
        if (autoSubmitRes.ok) {
          const autoSubmitData = await autoSubmitRes.json();
          if (autoSubmitData.auto_submit_enabled) {
            // Wait a moment for the form to settle, then click submit
            await new Promise(r => setTimeout(r, 2000));
            autoSubmitted = await clickSubmitButton();

            // If we found a matching queue item, submit a receipt
            if (autoSubmitted && tailoredCvPdfUrl) {
              const queueRes = await fetch(`${API_BASE}/auto-apply/queue`, {
                headers: { Authorization: `Bearer ${jobscale_token}` }
              });
              if (queueRes.ok) {
                const queueData = await queueRes.json();
                const currentUrl = window.location.href;
                const matching = (queueData.queue || []).find(q => {
                  if (!q.job || !q.job.external_url) return false;
                  return q.job.external_url.split('?')[0] === currentUrl.split('?')[0]
                    || currentUrl.includes(q.job.external_url.split('?')[0]);
                });
                if (matching) {
                  // Submit receipt
                  await fetch(`${API_BASE}/auto-apply/queue/${matching.id}/receipt`, {
                    method: 'POST',
                    headers: {
                      'Content-Type': 'application/json',
                      Authorization: `Bearer ${jobscale_token}`
                    },
                    body: JSON.stringify({
                      fields_filled: data,
                      ats_type: ats,
                      ats_response: 'submitted',
                      submitted_at: new Date().toISOString(),
                    })
                  });
                  showToast('JobScale: ✓ Auto-submitted! Receipt saved.');

                  // Notify the background script that this tab is done
                  // (so the auto-session can close the tab and move to the next job)
                  try {
                    chrome.runtime.sendMessage({
                      action: 'autoSubmitComplete',
                      receipt: { queue_id: matching.id, ats_type: ats },
                    });
                  } catch (e) {
                    // Background script may not be listening if not in a session
                  }
                  return;
                }
              }
            }
          }
        }
      } catch (e) {
        console.log('Auto-submit check failed:', e);
      }

      // 5. Honest messaging — distinguish "filled + CV attached" from "nothing to fill"
      const hasProfileData = data.first_name || data.linkedin_url || (data.answers && Object.keys(data.answers).length > 0);
      if (tailoredCvPdfUrl && hasProfileData) {
        showToast('JobScale: form filled + tailored CV attached. Review and click Submit.');
      } else if (hasProfileData) {
        showToast('JobScale: form filled. (No matching queue item — CV not attached.) Review and click Submit.');
      } else if (tailoredCvPdfUrl) {
        showToast('JobScale: tailored CV attached. Fill in your details and click Submit.');
      } else {
        showToast('JobScale: no saved profile or matching queue item. Save your answers in Auto-Fill Settings first.', 'info');
      }
    } catch (e) {
      console.error('JobScale auto-fill error:', e);
      showToast('JobScale: auto-fill failed. You can fill manually.', 'error');
    }
  }

  // ===== INIT =====
  function init() {
    const ats = detectATS();
    if (!ats) return;

    // Show the auto-fill button once the page is ready.
    // We do NOT auto-run because:
    //  1. React SPA forms (Greenhouse/Lever) often aren't fully rendered at page load
    //  2. File attachment requires a user gesture in Chrome's security model
    //  3. Auto-filling before the user is ready feels intrusive
    // The user clicks the floating button when they're ready.
    const showButton = () => {
      if (document.body) {
        showAutoFillButton(autoFill);
      } else {
        setTimeout(showButton, 200);
      }
    };
    showButton();
  }

  // Run after a short delay to let the form render
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => setTimeout(init, 1200));
  } else {
    setTimeout(init, 1200);
  }
})();