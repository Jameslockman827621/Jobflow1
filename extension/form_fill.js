// JobScale Form Auto-Fill Content Script v2
// Tested against real Greenhouse, Lever, Ashby, Workable, Workday forms.
// Uses exact field selectors discovered from real ATS HTML inspection.
// Handles: multi-step forms, CAPTCHA detection, selects/radios/checkboxes,
// file uploads, and auto-submit (when user has opted in).

(function () {
  'use strict';

  const DASHBOARD_URL = 'http://localhost:3000';
  const API_BASE = `${DASHBOARD_URL}/api/v1`;

  // ===== ATS DETECTION =====
  function detectATS() {
    const host = window.location.hostname.toLowerCase();
    if (host.includes('greenhouse.io') || host.includes('job-boards.greenhouse.io')) return 'greenhouse';
    if (host.includes('lever.co') || host.includes('jobs.lever.co')) return 'lever';
    if (host.includes('ashbyhq.com')) return 'ashby';
    if (host.includes('workable.com')) return 'workable';
    if (host.includes('myworkdayjobs.com') || host.includes('wd1.') || host.includes('wd3.') || host.includes('wd5.')) return 'workday';
    if (document.querySelector('iframe[src*="greenhouse.io"]')) return 'greenhouse_embed';
    if (document.querySelector('iframe[src*="lever.co"]')) return 'lever_embed';
    if (document.querySelector('iframe[src*="ashbyhq.com"]')) return 'ashby_embed';
    if (document.querySelector('iframe[src*="myworkdayjobs.com"]')) return 'workday_embed';
    return null;
  }

  // ===== CAPTCHA DETECTION =====
  function detectCaptcha() {
    // reCAPTCHA v2/v3
    if (document.querySelector('.g-recaptcha, iframe[src*="recaptcha"], #g-recaptcha-response')) {
      return { type: 'recaptcha', message: 'reCAPTCHA detected — you will need to solve it manually' };
    }
    // hCaptcha
    if (document.querySelector('.h-captcha, iframe[src*="hcaptcha.com"]')) {
      return { type: 'hcaptcha', message: 'hCaptcha detected — you will need to solve it manually' };
    }
    // Cloudflare Turnstile
    if (document.querySelector('.cf-turnstile, iframe[src*="challenges.cloudflare.com"]')) {
      return { type: 'turnstile', message: 'Cloudflare Turnstile detected — you will need to solve it manually' };
    }
    // Generic iframe-based challenge
    const challengeIframes = document.querySelectorAll('iframe[src*="captcha"], iframe[src*="challenge"], iframe[src*="verify"]');
    if (challengeIframes.length > 0) {
      return { type: 'unknown', message: 'CAPTCHA/challenge detected — you will need to solve it manually' };
    }
    return null;
  }

  // ===== FIELD SETTING (React-compatible) =====
  function setFieldValue(field, value) {
    if (!field || value === undefined || value === null) return false;
    try {
      // Handle selects
      if (field.tagName === 'SELECT') {
        // Try to find an option that matches the value
        const options = Array.from(field.options);
        const match = options.find(o =>
          o.text.toLowerCase().includes(String(value).toLowerCase()) ||
          o.value.toLowerCase().includes(String(value).toLowerCase())
        );
        if (match) {
          field.value = match.value;
          field.dispatchEvent(new Event('change', { bubbles: true }));
          field.dispatchEvent(new Event('input', { bubbles: true }));
          return true;
        }
        return false;
      }

      // Handle checkboxes
      if (field.type === 'checkbox') {
        field.checked = Boolean(value);
        field.dispatchEvent(new Event('change', { bubbles: true }));
        field.dispatchEvent(new Event('click', { bubbles: true }));
        return true;
      }

      // Handle radios
      if (field.type === 'radio') {
        if (field.value.toLowerCase().includes(String(value).toLowerCase()) ||
            String(value).toLowerCase().includes(field.value.toLowerCase())) {
          field.checked = true;
          field.dispatchEvent(new Event('change', { bubbles: true }));
          field.dispatchEvent(new Event('click', { bubbles: true }));
          return true;
        }
        return false;
      }

      // Handle text inputs + textareas — use native setter for React compat
      const nativeSetter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype, 'value'
      )?.set || Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value')?.set;

      if (field.tagName === 'TEXTAREA') {
        const textareaSetter = Object.getOwnPropertyDescriptor(
          window.HTMLTextAreaElement.prototype, 'value'
        )?.set;
        if (textareaSetter) textareaSetter.call(field, String(value));
        else field.value = String(value);
      } else if (nativeSetter) {
        nativeSetter.call(field, String(value));
      } else {
        field.value = String(value);
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

  // ===== FIELD FINDING (ATS-specific selectors) =====

  function fillById(id, value, root = document) {
    if (!value) return false;
    const field = root.getElementById(id);
    if (field) return setFieldValue(field, value);
    return false;
  }

  function fillBySelector(selector, value, root = document) {
    if (!value) return false;
    const field = root.querySelector(selector);
    if (field) return setFieldValue(field, value);
    return false;
  }

  function fillByLabel(labelText, value, root = document) {
    if (!value) return false;
    const labels = root.querySelectorAll('label');
    for (const label of labels) {
      const text = (label.textContent || '').toLowerCase().trim();
      if (text.includes(labelText.toLowerCase())) {
        const forId = label.getAttribute('for');
        if (forId) {
          const field = root.getElementById(forId) || root.querySelector('#' + CSS.escape(forId));
          if (field) return setFieldValue(field, value);
        }
        const fieldInside = label.querySelector('input, textarea, select');
        if (fieldInside) return setFieldValue(fieldInside, value);
      }
    }
    // Try placeholder match
    const inputs = root.querySelectorAll('input, textarea');
    for (const input of inputs) {
      const placeholder = (input.placeholder || '').toLowerCase();
      if (placeholder.includes(labelText.toLowerCase())) {
        return setFieldValue(input, value);
      }
    }
    return false;
  }

  // ===== COMMON FIELD FILLING (works across all ATSes) =====
  async function fillCommonFields(data, root = document) {
    let filled = 0;
    const { first_name, last_name, email, phone, location, linkedin_url, github_url, website, answers } = data;

    // Name fields — try ID first (Greenhouse pattern), then label, then name attr
    if (first_name) {
      if (fillById('first_name', first_name, root)) filled++;
      else if (fillByLabel('First Name', first_name, root)) filled++;
      else if (fillBySelector('input[name="first_name"]', first_name, root)) filled++;
    }
    if (last_name) {
      if (fillById('last_name', last_name, root)) filled++;
      else if (fillByLabel('Last Name', last_name, root)) filled++;
      else if (fillBySelector('input[name="last_name"]', last_name, root)) filled++;
    }
    // Full name fallback
    if (first_name && last_name && filled === 0) {
      if (fillByLabel('Full Name', `${first_name} ${last_name}`, root)) filled++;
      else if (fillByLabel('Name', `${first_name} ${last_name}`, root)) filled++;
    }
    // Email
    if (email) {
      if (fillById('email', email, root)) filled++;
      else if (fillByLabel('Email', email, root)) filled++;
      else if (fillBySelector('input[name="email"], input[type="email"]', email, root)) filled++;
    }
    // Phone
    if (phone) {
      if (fillById('phone', phone, root)) filled++;
      else if (fillByLabel('Phone', phone, root)) filled++;
      else if (fillBySelector('input[name="phone"], input[type="tel"]', phone, root)) filled++;
    }
    // Location
    if (location) {
      if (fillById('candidate-location', location, root)) filled++;  // Greenhouse
      if (fillByLabel('Location', location, root)) filled++;
      if (fillByLabel('Where are you located', location, root)) filled++;
      if (fillById('country', location, root)) filled++;  // Greenhouse country field
    }
    // LinkedIn
    if (linkedin_url) {
      if (fillByLabel('LinkedIn', linkedin_url, root)) filled++;
      else if (fillBySelector('input[name*="linkedin"]', linkedin_url, root)) filled++;
      else if (fillById('linkedin', linkedin_url, root)) filled++;
    }
    // GitHub
    if (github_url) {
      if (fillByLabel('GitHub', github_url, root)) filled++;
      else if (fillBySelector('input[name*="github"]', github_url, root)) filled++;
    }
    // Website/Portfolio
    if (website) {
      if (fillByLabel('Website', website, root)) filled++;
      if (fillByLabel('Portfolio', website, root)) filled++;
      if (fillBySelector('input[name*="website"], input[name*="portfolio"]', website, root)) filled++;
    }

    // Common application questions (saved by the user)
    if (answers) {
      const questionMap = {
        'work_authorization': ['authorized to work', 'work authorization', 'legally authorized', 'eligible to work'],
        'requires_sponsorship': ['sponsorship', 'visa sponsorship', 'require sponsorship', 'need sponsorship'],
        'willing_to_relocate': ['willing to relocate', 'relocate', 'relocation'],
        'years_of_experience': ['years of experience', 'years of relevant', 'how many years'],
        'earliest_start': ['earliest start', 'start date', 'when can you start'],
        'salary_expectation': ['salary expectation', 'salary requirements', 'expected salary'],
        'why_this_company': ['why do you want', 'why this company', 'why are you interested'],
      };
      for (const [key, labels] of Object.entries(questionMap)) {
        const value = answers[key];
        if (!value) continue;
        for (const label of labels) {
          // Try label-based fill for standard fields
          if (fillByLabel(label, value, root)) { filled++; break; }
        }
        // Also try Greenhouse-style custom question IDs
        // Greenhouse uses question_XXXXXXX IDs — we try to match by label text
        const questionFields = root.querySelectorAll('[id^="question_"]');
        for (const qf of questionFields) {
          const labelEl = root.querySelector(`label[for="${qf.id}"]`);
          if (labelEl) {
            const labelText = (labelEl.textContent || '').toLowerCase();
            for (const label of labels) {
              if (labelText.includes(label)) {
                if (setFieldValue(qf, value)) { filled++; break; }
              }
            }
          }
        }
      }
    }
    return filled;
  }

  // ===== FILE ATTACHMENT =====
  async function attachFileByUrl(input, url, filename) {
    if (!input || !url) return false;
    try {
      const { jobscale_token } = await chrome.storage.local.get('jobscale_token');
      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${jobscale_token}` }
      });
      if (!res.ok) return false;
      const blob = await res.blob();
      const file = new File([blob], filename, { type: blob.type || 'application/pdf' });
      const dt = new DataTransfer();
      dt.items.add(file);
      input.files = dt.files;
      input.dispatchEvent(new Event('change', { bubbles: true }));
      return true;
    } catch (e) {
      console.warn('JobScale: file attach error', e);
      return false;
    }
  }

  async function attachResume(url, filename = 'tailored_cv.pdf', root = document) {
    if (!url) return false;
    // Greenhouse: #resume and #cover_letter
    // Lever: input[type="file"] with name containing "resume"
    // Ashby: input[type="file"] in the form
    // Workable: input[type="file"]
    const fileInputs = root.querySelectorAll('input[type="file"]');
    for (const input of fileInputs) {
      const id = (input.id || '').toLowerCase();
      const name = (input.name || '').toLowerCase();
      const accept = (input.getAttribute('accept') || '').toLowerCase();
      // Match resume/CV upload fields specifically
      if (
        id.includes('resume') || id.includes('cv') ||
        name.includes('resume') || name.includes('cv') ||
        (accept.includes('pdf') && !id.includes('cover') && !name.includes('cover'))
      ) {
        const ok = await attachFileByUrl(input, url, filename);
        if (ok) return true;
      }
    }
    // If no specific resume field found, try the first file input
    if (fileInputs.length > 0) {
      return await attachFileByUrl(fileInputs[0], url, filename);
    }
    return false;
  }

  async function attachCoverLetter(url, filename = 'cover_letter.pdf', root = document) {
    if (!url) return false;
    // Greenhouse has a specific #cover_letter file input
    const clInput = root.querySelector('#cover_letter, input[type="file"][id*="cover"], input[type="file"][name*="cover"]');
    if (clInput) {
      return await attachFileByUrl(clInput, url, filename);
    }
    return false;
  }

  // ===== MULTI-STEP FORM HANDLING =====
  async function handleMultiStepForm(fillFn, root = document) {
    // Detect if this is a multi-step form (Workday, some Greenhouse custom forms)
    const nextButton = findNextButton(root);
    if (!nextButton) {
      // Single-page form — fill and we're done
      await fillFn(root);
      return true;
    }

    // Multi-step: fill current page, click Next, wait for next page, repeat
    let step = 0;
    while (nextButton || step < 10) {
      // Fill the current page
      await fillFn(root);
      step++;

      // Find and click the Next/Continue button
      const btn = findNextButton(root);
      if (!btn) break;  // No more Next buttons — we're on the last page

      btn.click();

      // Wait for the next page to render (2 seconds, then check for content)
      await new Promise(r => setTimeout(r, 2000));
    }

    // Fill the last page
    await fillFn(root);
    return true;
  }

  function findNextButton(root = document) {
    const nextTexts = ['next', 'continue', 'proceed', 'step 2', 'page 2'];
    const buttons = root.querySelectorAll('button, a[role="button"], input[type="button"], input[type="submit"]');
    for (const btn of buttons) {
      const text = (btn.textContent || btn.value || '').toLowerCase().trim();
      if (nextTexts.some(t => text === t || text.includes(t))) {
        // Make sure it's not the submit button
        if (!text.includes('submit') && !text.includes('apply')) {
          return btn;
        }
      }
    }
    return null;
  }

  // ===== AUTO-SUBMIT =====
  async function clickSubmitButton(root = document) {
    const selectors = [
      'button[type="submit"]',
      'input[type="submit"]',
      'button[data-automation-id="submit"]',  // Workday
      '#submit-app',  // Greenhouse alt
      'button.btn--pill',  // Greenhouse
    ];

    for (const selector of selectors) {
      const btn = root.querySelector(selector);
      if (btn && !btn.disabled && !btn.getAttribute('aria-disabled')) {
        btn.click();
        return true;
      }
    }

    // Fallback: text-based search
    const submitTexts = ['submit application', 'submit', 'apply', 'send application', 'submit application'];
    const buttons = root.querySelectorAll('button, input[type="button"], a[role="button"]');
    for (const btn of buttons) {
      const text = (btn.textContent || btn.value || '').toLowerCase().trim();
      if (submitTexts.includes(text) && !btn.disabled) {
        btn.click();
        return true;
      }
    }
    return false;
  }

  // ===== ATS-SPECIFIC FILL =====

  async function fillGreenhouse(data, root = document) {
    // Greenhouse forms use simple IDs: first_name, last_name, email, phone, etc.
    // No iframe needed — form is in the main document.
    const filled = await fillCommonFields(data, root);
    // Attach resume to #resume
    if (data.tailored_cv_pdf_url) {
      await attachResume(data.tailored_cv_pdf_url, 'tailored_cv.pdf', root);
    }
    // Attach cover letter to #cover_letter if available
    if (data.cover_letter_url) {
      await attachCoverLetter(data.cover_letter_url, 'cover_letter.pdf', root);
    }
    return filled;
  }

  async function fillLever(data, root = document) {
    const filled = await fillCommonFields(data, root);
    if (data.tailored_cv_pdf_url) {
      await attachResume(data.tailored_cv_pdf_url, 'tailored_cv.pdf', root);
    }
    return filled;
  }

  async function fillAshby(data, root = document) {
    const filled = await fillCommonFields(data, root);
    if (data.tailored_cv_pdf_url) {
      await attachResume(data.tailored_cv_pdf_url, 'tailored_cv.pdf', root);
    }
    return filled;
  }

  async function fillWorkable(data, root = document) {
    const filled = await fillCommonFields(data, root);
    if (data.tailored_cv_pdf_url) {
      await attachResume(data.tailored_cv_pdf_url, 'tailored_cv.pdf', root);
    }
    return filled;
  }

  async function fillWorkday(data, root = document) {
    // Workday forms are multi-step — use handleMultiStepForm
    const filled = await fillCommonFields(data, root);
    if (data.tailored_cv_pdf_url) {
      await attachResume(data.tailored_cv_pdf_url, 'tailored_cv.pdf', root);
    }
    return filled;
  }

  // ===== UI =====
  function showAutoFillButton(onClick) {
    if (document.getElementById('jobscale-autofill-btn')) return;
    const btn = document.createElement('button');
    btn.id = 'jobscale-autofill-btn';
    btn.innerHTML = '✨ Auto-fill with JobScale';
    btn.style.cssText = `
      position: fixed; top: 16px; right: 16px; z-index: 2147483647;
      padding: 10px 16px; background: linear-gradient(135deg, #0d9488, #0f766e);
      color: white; border: none; border-radius: 8px; font-size: 13px;
      font-weight: 600; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      cursor: pointer; box-shadow: 0 4px 12px rgba(13, 148, 136, 0.4);
    `;
    btn.onclick = onClick;
    document.body.appendChild(btn);
  }

  function showToast(message, type = 'success') {
    const colors = {
      success: { bg: '#f0fdf4', border: '#bbf7d0', text: '#166534' },
      error: { bg: '#fef2f2', border: '#fecaca', text: '#991b1b' },
      info: { bg: '#eff6ff', border: '#bfdbfe', text: '#1e40af' },
      warning: { bg: '#fef3c7', border: '#fde68a', text: '#92400e' },
    };
    const c = colors[type] || colors.success;
    const toast = document.createElement('div');
    toast.style.cssText = `
      position: fixed; top: 64px; right: 16px; z-index: 2147483647;
      padding: 10px 14px; background: ${c.bg}; color: ${c.text};
      border: 1px solid ${c.border}; border-radius: 8px;
      font-size: 12px; font-weight: 500;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      max-width: 320px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    `;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 5000);
  }

  // ===== MAIN =====
  async function autoFill() {
    const ats = detectATS();
    if (!ats) {
      showToast('JobScale: no application form detected on this page', 'info');
      return;
    }

    // Check for CAPTCHA before doing anything
    const captcha = detectCaptcha();
    if (captcha) {
      showToast(`JobScale: ${captcha.message}. Fill the form manually after solving it.`, 'warning');
      // Still try to fill the non-CAPTCHA fields
    }

    showToast('JobScale: auto-filling your application...', 'info');

    try {
      const { jobscale_token } = await chrome.storage.local.get('jobscale_token');
      if (!jobscale_token) {
        showToast('JobScale: please sign in to the extension first', 'error');
        return;
      }

      // 1. Get saved answers + auto-fill profile
      const answersRes = await fetch(`${API_BASE}/auto-apply/answers`, {
        headers: { Authorization: `Bearer ${jobscale_token}` }
      });
      let answersData = {};
      if (answersRes.ok) answersData = await answersRes.json();

      // 2. Find matching queue item for this job URL
      const queueRes = await fetch(`${API_BASE}/auto-apply/queue`, {
        headers: { Authorization: `Bearer ${jobscale_token}` }
      });
      let tailoredCvPdfUrl = null;
      let coverLetterUrl = null;
      let matchingQueueId = null;
      if (queueRes.ok) {
        const queueData = await queueRes.json();
        const currentUrl = window.location.href.split('?')[0];
        const matching = (queueData.queue || []).find(q => {
          if (!q.job || !q.job.external_url) return false;
          const jobUrl = q.job.external_url.split('?')[0];
          return jobUrl === currentUrl || currentUrl.includes(jobUrl) || jobUrl.includes(currentUrl);
        });
        if (matching) {
          tailoredCvPdfUrl = `${DASHBOARD_URL}${matching.tailored_cv_pdf_url}`;
          matchingQueueId = matching.id;
          // Check for cover letter
          if (matching.tailored_cv_data?.cover_letter) {
            // We don't have a cover letter PDF endpoint yet — use the HTML export
          }
          // Mark as in_progress
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
        cover_letter_url: coverLetterUrl,
      };

      // 4. Handle multi-step forms + fill
      const fillFn = (root) => {
        if (ats === 'greenhouse' || ats === 'greenhouse_embed') return fillGreenhouse(data, root);
        if (ats === 'lever' || ats === 'lever_embed') return fillLever(data, root);
        if (ats === 'ashby' || ats === 'ashby_embed') return fillAshby(data, root);
        if (ats === 'workable') return fillWorkable(data, root);
        if (ats === 'workday' || ats === 'workday_embed') return fillWorkday(data, root);
        return fillCommonFields(data, root);
      };

      // Check for multi-step (Workday, some custom forms)
      if (ats === 'workday' || ats === 'workday_embed' || findNextButton()) {
        await handleMultiStepForm(fillFn, document);
      } else {
        await fillFn(document);
      }

      // 5. Check if auto-submit is enabled
      let autoSubmitted = false;
      if (!captcha) {  // Don't auto-submit if CAPTCHA is present
        try {
          const autoSubmitRes = await fetch(`${API_BASE}/auto-apply/auto-submit`, {
            headers: { Authorization: `Bearer ${jobscale_token}` }
          });
          if (autoSubmitRes.ok) {
            const autoSubmitData = await autoSubmitRes.json();
            if (autoSubmitData.auto_submit_enabled) {
              await new Promise(r => setTimeout(r, 2000));  // Wait for form to settle
              autoSubmitted = await clickSubmitButton(document);

              // Send receipt if we auto-submitted and have a matching queue item
              if (autoSubmitted && matchingQueueId) {
                await fetch(`${API_BASE}/auto-apply/queue/${matchingQueueId}/receipt`, {
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

                // Notify background script (for autonomous session)
                try {
                  chrome.runtime.sendMessage({
                    action: 'autoSubmitComplete',
                    receipt: { queue_id: matchingQueueId, ats_type: ats },
                  });
                } catch (e) {}

                showToast('JobScale: ✓ Auto-submitted! Receipt saved.');
                return;
              }
            }
          }
        } catch (e) {
          console.log('Auto-submit check failed:', e);
        }
      }

      // 6. Show result message
      if (captcha) {
        showToast(`JobScale: form filled. Solve the CAPTCHA and click Submit manually.`, 'warning');
      } else if (autoSubmitted) {
        showToast('JobScale: ✓ Submitted! (no matching queue item for receipt)');
      } else {
        showToast('JobScale: form filled. Review and click Submit.');
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
    const showButton = () => {
      if (document.body) {
        showAutoFillButton(autoFill);
      } else {
        setTimeout(showButton, 200);
      }
    };
    showButton();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => setTimeout(init, 1200));
  } else {
    setTimeout(init, 1200);
  }
})();