# Tsenta Gap Closure — Honest Status

## Verified working (not scaffolding)

| Capability | Evidence |
|------------|----------|
| Account register/login/me | Live API + pytest |
| Greenhouse **live form fill** | Playwright filled `#first_name/#last_name/#email/#phone` + custom questions on real GitLab board; `core_ok=true`, **no submit** |
| Lever **live form fill** | Playwright filled Wealthfront `/apply` (`name/email/phone/linkedin`); pytest green |
| Headless apply via API | `POST /apply-engine/headless` on real Greenhouse URL → 11 fields, status `needs_user` |
| Company discovery | Probed 163 boards → **74 live** (~10.3k jobs est.), directory **388** monitored |
| Scale packaging | Batch-start **120** applications + hourly/daily quotas |
| Extension ATS selectors | Greenhouse/Lever/Workday-specific fill paths in `form-filler.js` |

## Still not Tsenta-class

| Gap | Reality |
|-----|---------|
| 50k career pages | **388** monitored + import/discovery pipeline — not 50k yet |
| Seconds-after-posting | Hot poll **60s**, not webhooks / true push |
| CAPTCHA solve in prod | Client wired; needs `TWOCAPTCHA_API_KEY`; fills stop at `needs_user` when CAPTCHA blocks submit |
| Auto-submit unattended | **Intentionally off by default** (legal + CAPTCHA). Enable only with keys + `HEADLESS_APPLY_AUTO_SUBMIT` |
| Workday 3–4 step mastery | Adapter exists (`data-automation-id`); listing pages often require picking a job / account — not at Greenhouse reliability yet |
| Ashby SPA | Adapter waits for React inputs; less proven than GH/Lever |
| WhatsApp / iMessage | Twilio + bridge adapters; need credentials / Mac host |
| Proxy evasion | Pool + fingerprints ready; empty without `PROXY_POOL` |
| Hundreds of **successful submits**/user | Packaging + quotas tested; live **submits** not load-tested (we don't spam employers) |

## Tests

```bash
cd backend
python -m pytest tests/test_apply_engine.py tests/test_tsenta_e2e.py \
  tests/test_scale_apply.py tests/test_live_ats_fill.py tests/test_smoke.py -v
```

**21 passed** including live Greenhouse + Lever fills.

## Env for production hardening

```
TWOCAPTCHA_API_KEY=
PROXY_POOL=http://user:pass@host:port,...
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_FROM=whatsapp:+1...
IMESSAGE_BRIDGE_URL=
HEADLESS_APPLY_ENABLED=true
HEADLESS_APPLY_AUTO_SUBMIT=false
```

Deploy images need: `playwright install --with-deps chromium` and Celery worker **+ beat**.
