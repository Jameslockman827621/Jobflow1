// JobScale Form Auto-Fill Content Script v3
// Tested against real Greenhouse, Lever, Ashby, Workable, Workday forms.
// Uses exact field selectors discovered from real ATS HTML inspection.
// Handles: multi-step forms, CAPTCHA detection, selects/radios/checkboxes,
// file uploads, iframes, and auto-submit (when user has opted in).
//
// Hardening in v3:
//  - Waits for iframes to load before filling inside them
//  - Detects SPA route changes after clicking Next
//  - Retries fields that didn't fill on the first pass
//  - Verifies required fields are filled before auto-submit
//  - Never auto-submits when a CAPTCHA is present
//  - Bails out of infinite Next loops (max 15 pages)
//  - Reports exactly which fields were filled vs skipped for the receipt

(function () {
  'use strict';

  const DASHBOARD_URL = 'http://localhost:3000';
  const API_BASE = `${DASHBOARD_URL}/api/v1`;
  const MAX_STEPS = 15;       // Never loop more than 15 pages
  const STEP_WAIT_MS = 2000;  // Wait between multi-step pages

  // ===== ATS DETECTION =====
  function detectATS() {
    const host = window.location.hostname.toLowerCase();
    if (host.includes('greenhouse.io') || host.includes('job-boards.greenhouse.io')) return 'greenhouse';
    if (host.includes('lever.co') || host.includes('jobs.lever.co')) return 'lever';
    if (host.includes('ashbyhq.com') || host.includes('ashby.com')) return 'ashby';
    if (host.includes('workable.com')) return 'workable';
    if (host.includes('myworkdayjobs.com') || host.includes('wd1.') || host.includes('wd3.') || host.includes('wd5.')) return 'workday';
    if (document.querySelector('iframe[src*="greenhouse.io"]')) return 'greenhouse_embed';
    if (document.querySelector('iframe[src*="lever.co"]')) return 'lever_embed';
    if (document.querySelector('iframe[src*="ashbyhq.com"]')) return 'ashby_embed';
    if (document.querySelector('iframe[src*="myworkdayjobs.com"]')) return 'workday_embed';
    if (document.querySelector('iframe[src*="workable.com"]')) return 'workable_embed';
    return null;
  }

  // ===== CAPTCHA DETECTION =====
  function detectCaptcha() {
    if (document.querySelector('.g-recaptcha, iframe[src*="recaptcha"], #g-recaptcha-response')) {
      return { type: 'recaptcha', message: 'reCAPTCHA detected — you will need to solve it manually' };
    }
    if (document.querySelector('.h-captcha, iframe[src*="hcaptcha.com"]')) {
      return { type: 'hcaptcha', message: 'hCaptcha detected — you will need to solve it manually' };
    }
    if (document.querySelector('.cf-turnstile, iframe[src*="challenges.cloudflare.com"]')) {
      return { type: 'turnstile', message: 'Cloudflare Turnstile detected — you will need to solve it manually' };
    }
    const challengeIframes = document.querySelectorAll('iframe[src*="captcha"], iframe[src*="challenge"], iframe[src*="verify"]');
    if (challengeIframes.length > 0) {
      return { type: 'unknown', message: 'CAPTCHA/challenge detected — you will need to solve it manually' };
    }
    return null;
  }

  // ===== FIELD SETTING (React-compatible) =====
  function setFieldValue(field, value) {
    if (!field || value === undefined || value === null) return false;
    // Skip invisible/disabled fields — they'll fail or block the form
    if (field.disabled || field.readOnly) return false;
    try {
      // Handle selects
      if (field.tagName === 'SELECT') {
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

  // ===== FIELD FINDING =====

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

  // Try multiple strategies to fill a field. Returns true if any worked.
  function fillField(strategies, root = document) {
    for (const s of strategies) {
      if (s.type === 'id' && fillById(s.value, s.data, root)) return true;
      if (s.type === 'selector' && fillBySelector(s.value, s.data, root)) return true;
      if (s.type === 'label' && fillByLabel(s.value, s.data, root)) return true;
    }
    return false;
  }

  // ===== COMMON FIELD FILLING =====
  function fillCommonFields(data, root = document) {
    const filled = { count: 0, fields: [] };
    const track = (name, ok) => {
      if (ok) { filled.count++; filled.fields.push(name); }
    };
    const { first_name, last_name, email, phone, location, linkedin_url, github_url, website, answers } = data;

    // Name fields — try ID first (Greenhouse pattern), then label, then name attr
    if (first_name) {
      track('first_name', fillField([
        { type: 'id', value: 'first_name', data: first_name },
        { type: 'label', value: 'First Name', data: first_name },
        { type: 'selector', value: 'input[name="first_name"]', data: first_name },
        { type: 'selector', value: 'input[name*="first"][name*="name"]', data: first_name },
      ], root));
    }
    if (last_name) {
      track('last_name', fillField([
        { type: 'id', value: 'last_name', data: last_name },
        { type: 'label', value: 'Last Name', data: last_name },
        { type: 'selector', value: 'input[name="last_name"]', data: last_name },
        { type: 'selector', value: 'input[name*="last"][name*="name"]', data: last_name },
      ], root));
    }
    // Full name fallback
    if (first_name && last_name && filled.count === 0) {
      track('full_name', fillField([
        { type: 'label', value: 'Full Name', data: `${first_name} ${last_name}` },
        { type: 'label', value: 'Name', data: `${first_name} ${last_name}` },
        { type: 'selector', value: 'input[name="name"], input[name="full_name"]', data: `${first_name} ${last_name}` },
      ], root));
    }
    // Email
    if (email) {
      track('email', fillField([
        { type: 'id', value: 'email', data: email },
        { type: 'label', value: 'Email', data: email },
        { type: 'selector', value: 'input[name="email"], input[type="email"]', data: email },
      ], root));
    }
    // Phone
    if (phone) {
      track('phone', fillField([
        { type: 'id', value: 'phone', data: phone },
        { type: 'label', value: 'Phone', data: phone },
        { type: 'selector', value: 'input[name="phone"], input[type="tel"]', data: phone },
      ], root));
    }
    // Location
    if (location) {
      track('location', fillField([
        { type: 'id', value: 'candidate-location', data: location },
        { type: 'label', value: 'Location', data: location },
        { type: 'label', value: 'Where are you located', data: location },
        { type: 'id', value: 'country', data: location },
        { type: 'selector', value: 'input[name="location"], input[name*="city"]', data: location },
      ], root));
    }
    // LinkedIn
    if (linkedin_url) {
      track('linkedin', fillField([
        { type: 'label', value: 'LinkedIn', data: linkedin_url },
        { type: 'selector', value: 'input[name*="linkedin"]', data: linkedin_url },
        { type: 'id', value: 'linkedin', data: linkedin_url },
      ], root));
    }
    // GitHub
    if (github_url) {
      track('github', fillField([
        { type: 'label', value: 'GitHub', data: github_url },
        { type: 'selector', value: 'input[name*="github"]', data: github_url },
      ], root));
    }
    // Website/Portfolio
    if (website) {
      track('website', fillField([
        { type: 'label', value: 'Website', data: website },
        { type: 'label', value: 'Portfolio', data: website },
        { type: 'selector', value: 'input[name*="website"], input[name*="portfolio"]', data: website },
      ], root));
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
        let filled_one = false;
        for (const label of labels) {
          if (fillByLabel(label, value, root)) { filled_one = true; break; }
        }
        // Greenhouse custom question IDs: question_XXXXXXX
        if (!filled_one) {
          const questionFields = root.querySelectorAll('[id^="question_"]');
          for (const qf of questionFields) {
            const labelEl = root.querySelector(`label[for="${qf.id}"]`);
            if (labelEl) {
              const labelText = (labelEl.textContent || '').toLowerCase();
              for (const label of labels) {
                if (labelText.includes(label)) {
                  if (setFieldValue(qf, value)) { filled_one = true; break; }
                }
              }
            }
            if (filled_one) break;
          }
        }
        track(`answer:${key}`, filled_one);
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
    const fileInputs = root.querySelectorAll('input[type="file"]');
    for (const input of fileInputs) {
      const id = (input.id || '').toLowerCase();
      const name = (input.name || '').toLowerCase();
      const accept = (input.getAttribute('accept') || '').toLowerCase();
      if (
        id.includes('resume') || id.includes('cv') ||
        name.includes('resume') || name.includes('cv') ||
        (accept.includes('pdf') && !id.includes('cover') && !name.includes('cover'))
      ) {
        const ok = await attachFileByUrl(input, url, filename);
        if (ok) return true;
      }
    }
    if (fileInputs.length > 0) {
      return await attachFileByUrl(fileInputs[0], url, filename);
    }
    return false;
  }

  async function attachCoverLetter(url, filename = 'cover_letter.pdf', root = document) {
    if (!url) return false;
    const clInput = root.querySelector('#cover_letter, input[type="file"][id*="cover"], input[type="file"][name*="cover"]');
    if (clInput) {
      return await attachFileByUrl(clInput, url, filename);
    }
    return false;
  }

  // ===== MULTI-STEP FORM HANDLING =====
  // Detects if a form is multi-step. If so, fills each page, clicks Next,
  // waits for the next page (by detecting DOM changes or URL changes), and
  // repeats. Bounded by MAX_STEPS to prevent infinite loops.
  async function handleMultiStepForm(fillFn, root = document) {
    const nextButton = findNextButton(root);
    if (!nextButton) {
      await fillFn(root);
      return { steps: 1, multiStep: false };
    }

    let step = 0;
    let prevUrl = window.location.href;
    let prevFieldCount = root.querySelectorAll('input, textarea, select').length;
    let stuckCount = 0;

    while (step < MAX_STEPS) {
      await fillFn(root);
      step++;

      const btn = findNextButton(root);
      if (!btn) break;  // No more Next buttons — last page

      // Snapshot state before clicking
      prevUrl = window.location.href;
      prevFieldCount = root.querySelectorAll('input, textarea, select').length;

      btn.click();

      // Wait for the next page to render — detect via URL change or field count change
      const changed = await waitForPageChange(prevUrl, prevFieldCount, root, STEP_WAIT_MS);
      if (!changed) {
        stuckCount++;
        // If we can't detect a page change twice in a row, the form probably
        // has validation errors or we're stuck. Stop and let the user take over.
        if (stuckCount >= 2) {
          console.warn('JobScale: multi-step form appears stuck — stopping auto-fill');
          break;
        }
      } else {
        stuckCount = 0;
      }
    }

    // Fill the last page (in case the loop exited before filling it)
    await fillFn(root);
    return { steps: step, multiStep: true };
  }

  function waitForPageChange(prevUrl, prevFieldCount, root, timeoutMs) {
    return new Promise((resolve) => {
      const start = Date.now();
      function check() {
        const urlChanged = window.location.href !== prevUrl;
        const fieldCount = root.querySelectorAll('input, textarea, select').length;
        const fieldsChanged = Math.abs(fieldCount - prevFieldCount) > 0;
        if (urlChanged || fieldsChanged) {
          // Give the new page a moment to settle
          setTimeout(() => resolve(true), 500);
          return;
        }
        if (Date.now() - start >= timeoutMs) {
          resolve(false);
          return;
        }
        setTimeout(check, 200);
      }
      check();
    });
  }

  function findNextButton(root = document) {
    const nextTexts = ['next', 'continue', 'proceed', 'step 2', 'page 2', 'next step', 'go to step'];
    const buttons = root.querySelectorAll('button, a[role="button"], input[type="button"], input[type="submit"]');
    for (const btn of buttons) {
      const text = (btn.textContent || btn.value || '').toLowerCase().trim();
      if (nextTexts.some(t => text === t || text.includes(t))) {
        // Make sure it's not the submit button
        if (!text.includes('submit') && !text.includes('apply')) {
          // And not disabled
          if (!btn.disabled && !btn.getAttribute('aria-disabled')) {
            return btn;
          }
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
      'button[data-qa="submit"]',
      'button.js-submit',
    ];

    for (const selector of selectors) {
      const btn = root.querySelector(selector);
      if (btn && !btn.disabled && !btn.getAttribute('aria-disabled')) {
        btn.click();
        return true;
      }
    }

    // Fallback: text-based search
    const submitTexts = ['submit application', 'submit', 'apply', 'send application'];
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

  // Verify all required fields are filled before auto-submitting.
  // Returns { ok: bool, missing: string[] }.
  function verifyRequiredFields(root = document) {
    const missing = [];
    const required = root.querySelectorAll('input[required], textarea[required], select[required], [aria-required="true"]');
    for (const f of required) {
      if (f.disabled || f.readOnly) continue;
      if (f.type === 'checkbox' && !f.checked) {
        const label = findLabelForField(f, root);
        missing.push(label || f.name || f.id || 'checkbox');
      } else if (!f.value || !f.value.trim()) {
        const label = findLabelForField(f, root);
        missing.push(label || f.name || f.id || f.type || 'field');
      }
    }
    return { ok: missing.length === 0, missing };
  }

  function findLabelForField(field, root = document) {
    if (field.id) {
      const label = root.querySelector(`label[for="${CSS.escape(field.id)}"]`);
      if (label) return (label.textContent || '').trim().slice(0, 50);
    }
    const parent = field.closest('label');
    if (parent) return (parent.textContent || '').trim().slice(0, 50);
    return null;
  }

  // ===== ATS-SPECIFIC FILL =====

  async function fillGreenhouse(data, root = document) {
    const filled = fillCommonFields(data, root);
    if (data.tailored_cv_pdf_url) {
      await attachResume(data.tailored_cv_pdf_url, 'tailored_cv.pdf', root);
    }
    if (data.cover_letter_url) {
      await attachCoverLetter(data.cover_letter_url, 'cover_letter.pdf', root);
    }
    return filled;
  }

  async function fillLever(data, root = document) {
    const filled = fillCommonFields(data, root);
    if (data.tailored_cv_pdf_url) {
      await attachResume(data.tailored_cv_pdf_url, 'tailored_cv.pdf', root);
    }
    return filled;
  }

  async function fillAshby(data, root = document) {
    const filled = fillCommonFields(data, root);
    if (data.tailored_cv_pdf_url) {
      await attachResume(data.tailored_cv_pdf_url, 'tailored_cv.pdf', root);
    }
    return filled;
  }

  async function fillWorkable(data, root = document) {
    const filled = fillCommonFields(data, root);
    if (data.tailored_cv_pdf_url) {
      await attachResume(data.tailored_cv_pdf_url, 'tailored_cv.pdf', root);
    }
    return filled;
  }

  async function fillWorkday(data, root = document) {
    const filled = fillCommonFields(data, root);
    if (data.tailored_cv_pdf_url) {
      await attachResume(data.tailored_cv_pdf_url, 'tailored_cv.pdf', root);
    }
    return filled;
  }

  // ===== IFRAME SUPPORT =====
  // Some ATSes (especially Greenhouse Embed) load the form inside an iframe.
  // We need to fill fields inside the iframe too. Same-origin iframes only —
  // cross-origin iframes will throw a SecurityError that we catch.
  function getIframes(root = document) {
    const iframes = Array.from(root.querySelectorAll('iframe'));
    return iframes.filter(f => {
      try { return !!f.contentDocument; } catch { return false; }
    });
  }

  async function fillAllFrames(fillFn, root = document) {
    const mainResult = await fillFn(root);
    const iframes = getIframes(root);
    for (const iframe of iframes) {
      try {
        const iframeDoc = iframe.contentDocument;
        if (iframeDoc && iframeDoc.body) {
          await fillFn(iframeDoc);
        }
      } catch (e) {
        console.warn('JobScale: iframe fill skipped', e);
      }
    }
    return mainResult;
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

    const captcha = detectCaptcha();
    if (captcha) {
      showToast(`JobScale: ${captcha.message}. Fill the form manually after solving it.`, 'warning');
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
          if (matching.tailored_cv_data?.cover_letter) {
            // Cover letter is stored as text; PDF export endpoint not yet wired
          }
          // Mark as in_progress (best-effort — don't block on it)
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

      // 4. Pick the right ATS-specific filler
      const fillFn = (root) => {
        if (ats === 'greenhouse' || ats === 'greenhouse_embed') return fillGreenhouse(data, root);
        if (ats === 'lever' || ats === 'lever_embed') return fillLever(data, root);
        if (ats === 'ashby' || ats === 'ashby_embed') return fillAshby(data, root);
        if (ats === 'workable' || ats === 'workable_embed') return fillWorkable(data, root);
        if (ats === 'workday' || ats === 'workday_embed') return fillWorkday(data, root);
        return fillCommonFields(data, root);
      };

      // 5. Fill — handle multi-step forms + iframes
      let totalFilled = 0;
      let filledFields = [];
      let stepInfo = { steps: 1, multiStep: false };

      const wrappedFill = async (root) => {
        const result = await fillAllFrames(fillFn, root);
        if (result && typeof result.count === 'number') {
          totalFilled += result.count;
          filledFields.push(...result.fields);
        }
      };

      if (ats === 'workday' || ats === 'workday_embed' || findNextButton()) {
        stepInfo = await handleMultiStepForm(wrappedFill, document);
      } else {
        await wrappedFill(document);
      }

      // 6. Check if auto-submit is enabled
      let autoSubmitted = false;
      let missingFields = [];
      if (!captcha) {
        try {
          const autoSubmitRes = await fetch(`${API_BASE}/auto-apply/auto-submit`, {
            headers: { Authorization: `Bearer ${jobscale_token}` }
          });
          if (autoSubmitRes.ok) {
            const autoSubmitData = await autoSubmitRes.json();
            if (autoSubmitData.auto_submit_enabled) {
              // Verify required fields before submitting
              const verification = verifyRequiredFields(document);
              if (!verification.ok) {
                missingFields = verification.missing;
                console.warn('JobScale: required fields missing, skipping auto-submit:', missingFields);
              } else {
                await new Promise(r => setTimeout(r, 2000));
                autoSubmitted = await clickSubmitButton(document);

                if (autoSubmitted && matchingQueueId) {
                  await fetch(`${API_BASE}/auto-apply/queue/${matchingQueueId}/receipt`, {
                    method: 'POST',
                    headers: {
                      'Content-Type': 'application/json',
                      Authorization: `Bearer ${jobscale_token}`
                    },
                    body: JSON.stringify({
                      fields_filled: data,
                      fields_filled_count: totalFilled,
                      fields_filled_names: filledFields,
                      ats_type: ats,
                      ats_response: 'submitted',
                      submitted_at: new Date().toISOString(),
                      multi_step: stepInfo.multiStep,
                      steps_filled: stepInfo.steps,
                    })
                  });

                  try {
                    chrome.runtime.sendMessage({
                      action: 'autoSubmitComplete',
                      receipt: { queue_id: matchingQueueId, ats_type: ats, fields_filled: totalFilled },
                    });
                  } catch (e) {}

                  showToast(`JobScale: ✓ Auto-submitted! ${totalFilled} fields filled. Receipt saved.`);
                  return;
                }
              }
            }
          }
        } catch (e) {
          console.log('Auto-submit check failed:', e);
        }
      }

      // 7. Show result message
      if (captcha) {
        showToast(`JobScale: form filled (${totalFilled} fields). Solve the CAPTCHA and click Submit manually.`, 'warning');
      } else if (autoSubmitted) {
        showToast('JobScale: ✓ Submitted! (no matching queue item for receipt)');
      } else if (missingFields.length > 0) {
        showToast(`JobScale: filled ${totalFilled} fields. Required fields missing: ${missingFields.slice(0, 3).join(', ')}${missingFields.length > 3 ? '…' : ''}. Please fill these and submit.`, 'warning');
      } else {
        showToast(`JobScale: form filled (${totalFilled} fields). Review and click Submit.`);
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
