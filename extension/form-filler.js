/**
 * JobScale Form Filler
 * Handles text, email, tel, select, radio, checkbox, textarea, file,
 * open-ended questions, CAPTCHA handoff, and multi-step ATS wizards
 * (Greenhouse / Lever / Workable / Ashby / Workday).
 */
(function () {
  'use strict';

  const API_BASE = 'http://localhost:8000/api/v1';

  function detectATS(url) {
    const u = (url || location.href).toLowerCase();
    if (u.includes('greenhouse')) return 'greenhouse';
    if (u.includes('lever.co')) return 'lever';
    if (u.includes('workable')) return 'workable';
    if (u.includes('ashbyhq')) return 'ashby';
    if (u.includes('myworkdayjobs') || u.includes('workday')) return 'workday';
    if (u.includes('linkedin.com')) return 'linkedin';
    if (u.includes('indeed.com')) return 'indeed';
    return 'generic';
  }

  function normalize(s) {
    return (s || '').toLowerCase().replace(/\s+/g, ' ').trim();
  }

  function labelFor(el) {
    if (!el) return '';
    if (el.labels && el.labels[0]) return el.labels[0].innerText;
    const id = el.id;
    if (id) {
      const lab = document.querySelector(`label[for="${CSS.escape(id)}"]`);
      if (lab) return lab.innerText;
    }
    const parent = el.closest('label, .field, .form-group, .application-field, [data-qa], li');
    return parent ? parent.innerText.slice(0, 240) : (el.name || el.placeholder || el.getAttribute('aria-label') || '');
  }

  function setNativeValue(el, value) {
    const proto = el.tagName === 'TEXTAREA'
      ? window.HTMLTextAreaElement.prototype
      : window.HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
    if (setter) setter.call(el, value);
    else el.value = value;
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
  }

  function matchKey(label, aliasesMap) {
    const n = normalize(label);
    for (const [key, aliases] of Object.entries(aliasesMap)) {
      for (const a of aliases) {
        if (n.includes(a) || a.includes(n)) return key;
      }
    }
    return null;
  }

  const ALIASES = {
    first_name: ['first name', 'firstname', 'first_name', 'given name', 'fname'],
    last_name: ['last name', 'lastname', 'last_name', 'surname', 'family name', 'lname'],
    full_name: ['full name', 'name', 'your name', 'applicant name'],
    email: ['email', 'e-mail', 'email address'],
    phone: ['phone', 'telephone', 'mobile', 'phone number', 'cell', 'tel'],
    linkedin: ['linkedin', 'linkedin url', 'linkedin profile'],
    portfolio: ['portfolio', 'website', 'github', 'personal website'],
    location: ['location', 'city', 'current location'],
    current_company: ['current company', 'employer', 'company'],
    current_title: ['current title', 'job title', 'current role'],
    resume: ['resume', 'cv', 'upload resume', 'attach resume'],
    cover_letter: ['cover letter', 'coverletter'],
    salary: ['salary', 'expected salary', 'compensation', 'desired salary'],
    work_auth: ['authorized', 'work authorization', 'legally authorized'],
    sponsorship: ['sponsorship', 'visa sponsorship', 'require sponsorship'],
  };

  function fillInput(el, value) {
    if (value == null || value === '') return false;
    const type = (el.type || '').toLowerCase();
    if (type === 'checkbox') {
      const want = ['1', 'true', 'yes', 'on'].includes(String(value).toLowerCase());
      if (el.checked !== want) el.click();
      return true;
    }
    if (type === 'radio') {
      const n = normalize(el.value + ' ' + labelFor(el));
      if (n.includes(normalize(String(value))) || (String(value).toLowerCase() === 'yes' && n.includes('yes'))) {
        el.click();
        return true;
      }
      return false;
    }
    if (type === 'file') return false; // handled separately
    setNativeValue(el, String(value));
    return true;
  }

  function fillSelect(el, value) {
    if (value == null || value === '') return false;
    const opts = Array.from(el.options || []);
    const target = normalize(String(value));
    let match = opts.find(o => normalize(o.text) === target || normalize(o.value) === target);
    if (!match) match = opts.find(o => normalize(o.text).includes(target) || target.includes(normalize(o.text)));
    if (!match && ['yes', 'true', '1'].includes(target)) {
      match = opts.find(o => ['yes', 'true', 'y'].includes(normalize(o.text)));
    }
    if (!match && ['no', 'false', '0'].includes(target)) {
      match = opts.find(o => ['no', 'false', 'n'].includes(normalize(o.text)));
    }
    if (!match) return false;
    el.value = match.value;
    el.dispatchEvent(new Event('change', { bubbles: true }));
    return true;
  }

  async function answerOpenEnded(token, question, jobId) {
    try {
      const res = await fetch(`${API_BASE}/apply-engine/answer`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question, job_id: jobId || null }),
      });
      if (!res.ok) return '';
      const data = await res.json();
      return data.answer || '';
    } catch (e) {
      return '';
    }
  }

  async function solveCaptcha(token, siteKey, pageUrl, captchaType) {
    try {
      const res = await fetch(`${API_BASE}/apply-engine/captcha/solve`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          captcha_type: captchaType || 'recaptcha_v2',
          site_key: siteKey,
          page_url: pageUrl,
        }),
      });
      return await res.json();
    } catch (e) {
      return { ok: false, error: String(e) };
    }
  }

  function findSiteKey() {
    const el = document.querySelector('[data-sitekey]');
    if (el) return el.getAttribute('data-sitekey');
    const iframe = document.querySelector('iframe[src*="recaptcha"], iframe[src*="hcaptcha"]');
    if (!iframe) return null;
    const src = iframe.getAttribute('src') || '';
    const m = src.match(/[?&]k=([^&]+)/);
    return m ? decodeURIComponent(m[1]) : null;
  }

  function injectCaptchaToken(token) {
    const areas = [
      document.querySelector('#g-recaptcha-response'),
      document.querySelector('[name="g-recaptcha-response"]'),
      document.querySelector('[name="h-captcha-response"]'),
      document.querySelector('textarea[name="h-captcha-response"]'),
    ].filter(Boolean);
    for (const el of areas) {
      el.value = token;
      el.dispatchEvent(new Event('input', { bubbles: true }));
    }
  }

  function clickNext(plan) {
    const selectors = (plan && plan.next_button_selectors) || [
      "button[type='submit']",
      "input[type='submit']",
      "#submit_app",
      "button.application-button",
      "[data-automation-id='bottom-navigation-next-button']",
    ];
    const textButtons = Array.from(document.querySelectorAll('button, a, input[type="button"]'));
    for (const el of textButtons) {
      const t = normalize(el.innerText || el.value || '');
      if (['next', 'continue', 'save and continue', 'review'].includes(t) || t.startsWith('next')) {
        el.click();
        return true;
      }
    }
    for (const sel of selectors) {
      try {
        const el = document.querySelector(sel);
        if (el && !el.disabled) {
          el.click();
          return true;
        }
      } catch (e) { /* ignore invalid selectors from Playwright-style */ }
    }
    return false;
  }

  function fillByIdOrSel(sel, value) {
    if (value == null || value === '') return false;
    const el = document.querySelector(sel);
    if (!el || el.disabled) return false;
    if (el.tagName === 'SELECT') return fillSelect(el, value);
    return fillInput(el, value);
  }

  function fillGreenhouse(applicant) {
    let n = 0;
    const pairs = [
      ['#first_name', applicant.first_name],
      ['#last_name', applicant.last_name],
      ['#email', applicant.email],
      ['#phone', applicant.phone],
      ["input[autocomplete='given-name']", applicant.first_name],
      ["input[autocomplete='family-name']", applicant.last_name],
      ["input[aria-label='First Name']", applicant.first_name],
      ["input[aria-label='Last Name']", applicant.last_name],
      ["input[aria-label='Email']", applicant.email],
      ["input[aria-label='Phone']", applicant.phone],
      ["input[aria-label*='LinkedIn' i]", applicant.linkedin],
    ];
    const seen = new Set();
    for (const [sel, val] of pairs) {
      const el = document.querySelector(sel);
      if (!el || seen.has(el)) continue;
      if (fillByIdOrSel(sel, val)) {
        seen.add(el);
        n += 1;
      }
    }
    // Custom questions
    document.querySelectorAll("input[id^='question_'], textarea[id^='question_']").forEach((el) => {
      if (el.value && el.value.trim()) return;
      const label = normalize((el.getAttribute('aria-label') || labelFor(el) || ''));
      if (label.includes('linkedin') && applicant.linkedin) {
        setNativeValue(el, applicant.linkedin); n += 1;
      } else if (label.includes('sponsor') || label.includes('visa')) {
        setNativeValue(el, 'No'); n += 1;
      } else if (label.includes('authorized') || label.includes('legally')) {
        setNativeValue(el, 'Yes'); n += 1;
      }
    });
    return n;
  }

  function fillLever(applicant) {
    let n = 0;
    const pairs = [
      ["input[name='name']", applicant.full_name],
      ["input[name='email']", applicant.email],
      ["input[name='phone']", applicant.phone],
      ["#location-input", applicant.location],
      ["input[name='org']", applicant.current_company],
      ["input[name=\"urls[LinkedIn]\"]", applicant.linkedin],
      ["input[name=\"urls[Portfolio]\"]", applicant.portfolio],
    ];
    for (const [sel, val] of pairs) {
      if (fillByIdOrSel(sel, val)) n += 1;
    }
    // Radios: leave to generic pass; selects: pick first meaningful
    document.querySelectorAll('select').forEach((el) => {
      if (el.value) return;
      const opt = Array.from(el.options).find(o => o.value && !['', 'select...', 'select'].includes(normalize(o.text)));
      if (opt) { el.value = opt.value; el.dispatchEvent(new Event('change', { bubbles: true })); n += 1; }
    });
    return n;
  }

  function fillWorkday(applicant) {
    let n = 0;
    const pairs = [
      ["[data-automation-id='legalNameSection_firstName']", applicant.first_name],
      ["[data-automation-id='legalNameSection_lastName']", applicant.last_name],
      ["[data-automation-id='email']", applicant.email],
      ["input[data-automation-id*='phone' i]", applicant.phone],
      ["input[type='email']", applicant.email],
      ["input[type='tel']", applicant.phone],
      ["input[aria-label*='First Name' i]", applicant.first_name],
      ["input[aria-label*='Last Name' i]", applicant.last_name],
    ];
    for (const [sel, val] of pairs) {
      if (fillByIdOrSel(sel, val)) n += 1;
    }
    return n;
  }

  async function fillPage(packageData, token) {
    const applicant = packageData.applicant || {};
    const plan = packageData.fill_plan || {};
    let filled = 0;
    const ats = detectATS();

    if (ats === 'greenhouse') filled += fillGreenhouse(applicant);
    else if (ats === 'lever') filled += fillLever(applicant);
    else if (ats === 'workday') filled += fillWorkday(applicant);

    // Map planned fields first
    for (const field of (plan.fields || [])) {
      const key = field.key;
      const value = field.value;
      if (value == null || value === '') continue;
      const inputs = Array.from(document.querySelectorAll('input, textarea, select'));
      for (const el of inputs) {
        if (el.type === 'hidden' || el.disabled) continue;
        const keyHit = matchKey(labelFor(el) + ' ' + (el.name || '') + ' ' + (el.id || ''), { [key]: ALIASES[key] || [key] });
        if (!keyHit) continue;
        if (el.tagName === 'SELECT') {
          if (fillSelect(el, value)) filled += 1;
        } else if (fillInput(el, value)) {
          filled += 1;
        }
        break;
      }
    }

    // Generic pass for unlabeled common fields
    const controls = Array.from(document.querySelectorAll('input, textarea, select'));
    for (const el of controls) {
      if (el.type === 'hidden' || el.disabled) continue;
      const key = matchKey(labelFor(el) + ' ' + (el.name || '') + ' ' + (el.id || '') + ' ' + (el.placeholder || ''), ALIASES);
      if (!key) continue;
      let value = applicant[key];
      if (key === 'work_auth') value = 'Yes';
      if (key === 'sponsorship') value = 'No';
      if (key === 'salary') {
        value = applicant.min_salary && applicant.max_salary
          ? `${applicant.min_salary}-${applicant.max_salary}`
          : (applicant.max_salary || applicant.min_salary || '');
      }
      if (value == null || value === '') continue;
      if (el.tagName === 'SELECT') {
        if (fillSelect(el, value)) filled += 1;
      } else if (el.type === 'radio' || el.type === 'checkbox') {
        if (fillInput(el, value)) filled += 1;
      } else if (!el.value) {
        if (fillInput(el, value)) filled += 1;
      }
    }

    // Open-ended textareas still empty
    for (const ta of Array.from(document.querySelectorAll('textarea'))) {
      if (ta.value && ta.value.trim()) continue;
      const q = labelFor(ta);
      if (!q || q.length < 12) continue;
      const answer = await answerOpenEnded(token, q, packageData.job_id);
      if (answer) {
        setNativeValue(ta, answer);
        filled += 1;
      }
    }

    // CAPTCHA
    let captcha = null;
    const siteKey = findSiteKey();
    if (siteKey) {
      const isH = !!document.querySelector('iframe[src*="hcaptcha"]');
      captcha = await solveCaptcha(token, siteKey, location.href, isH ? 'hcaptcha' : 'recaptcha_v2');
      if (captcha && captcha.ok && captcha.token) {
        injectCaptchaToken(captcha.token);
      }
    }

    return { filled, captcha };
  }

  async function runMultiStep(packageData, token) {
    const plan = packageData.fill_plan || {};
    const maxSteps = plan.max_steps || (detectATS() === 'workday' ? 6 : 4);
    let steps = 0;
    let fields = 0;
    let lastCaptcha = null;

    for (let i = 0; i < maxSteps; i += 1) {
      steps += 1;
      const result = await fillPage(packageData, token);
      fields += result.filled;
      lastCaptcha = result.captcha;
      showToast(`JobScale: filled step ${steps} (${result.filled} fields)`);
      if (!plan.multi_step && detectATS() !== 'workday') break;
      await sleep(800);
      const advanced = clickNext(plan);
      if (!advanced) break;
      await sleep(1400);
    }

    return { steps, fields, captcha: lastCaptcha, ats: detectATS() };
  }

  function sleep(ms) {
    return new Promise(r => setTimeout(r, ms));
  }

  function showToast(msg) {
    let el = document.getElementById('jobscale-toast');
    if (!el) {
      el = document.createElement('div');
      el.id = 'jobscale-toast';
      el.style.cssText = 'position:fixed;bottom:80px;right:20px;z-index:100000;background:#0f172a;color:#fff;padding:12px 16px;border-radius:10px;font:14px/1.4 system-ui;box-shadow:0 8px 24px rgba(0,0,0,.25);max-width:320px';
      document.body.appendChild(el);
    }
    el.textContent = msg;
    clearTimeout(el._t);
    el._t = setTimeout(() => el.remove(), 5000);
  }

  async function getToken() {
    return new Promise((resolve) => {
      try {
        chrome.runtime.sendMessage({ action: 'getToken' }, (resp) => {
          resolve((resp && resp.token) || null);
        });
      } catch (e) {
        resolve(null);
      }
    });
  }

  async function autoFillFromJobScale(applicationId) {
    const token = await getToken();
    if (!token) {
      showToast('JobScale: sign in via dashboard first');
      return { ok: false, error: 'not_authenticated' };
    }
    const url = applicationId
      ? `${API_BASE}/apply-engine/package/application/${applicationId}`
      : null;
    if (!url) {
      showToast('JobScale: missing application id');
      return { ok: false, error: 'missing_application' };
    }
    const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
    if (!res.ok) {
      showToast('JobScale: failed to load apply package');
      return { ok: false, error: 'package_failed' };
    }
    const packageData = await res.json();
    const result = await runMultiStep(packageData, token);
    showToast(`JobScale: done — ${result.fields} fields across ${result.steps} step(s). Review & submit.`);
    chrome.runtime.sendMessage({
      action: 'applyFillComplete',
      applicationId,
      result,
    });
    return { ok: true, ...result };
  }

  // Expose for content script / popup
  window.JobScaleFormFiller = {
    detectATS,
    fillPage,
    runMultiStep,
    autoFillFromJobScale,
    showToast,
  };

  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg && msg.action === 'fillApplication') {
      autoFillFromJobScale(msg.applicationId).then(sendResponse);
      return true;
    }
  });
})();
