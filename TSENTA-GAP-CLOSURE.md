# Tsenta Gap Closure — Honest Status (final matrix)

## Verified working (not scaffolding)

| Capability | Evidence |
|------------|----------|
| Account register/login/me | Live API + pytest |
| Greenhouse **live form fill** | Playwright filled `#first_name/#last_name/#email/#phone` + custom questions on real GitLab board; `core_ok=true`, **no submit** |
| Lever **live form fill** | Playwright filled Wealthfront `/apply` (`name/email/phone/linkedin`); pytest green |
| Headless apply via API | `POST /apply-engine/headless` on real Greenhouse URL → fields filled, status `needs_user` |
| Headless **batch queue** | `POST /apply-engine/headless/batch` enqueues Celery `apply_batch` (dry_run / live) |
| Dashboard Automation panel | Coverage + quota + last run; optional “Queue headless apply” after batch-start |
| Company discovery | Probed boards → live directory; coverage API exposes monitored page count |
| Scale packaging | Batch-start many applications + hourly/daily quotas; `scripts/scale_apply_smoke.py` |
| Extension ATS selectors | Greenhouse/Lever/Workday-specific fill paths in `form-filler.js` |
| Health `/ready` | DB hard check; Redis degraded-ok; captcha / proxy / messaging / `HEADLESS_APPLY_ENABLED` |
| Deploy packaging | `backend/Dockerfile` installs Chromium via `playwright install --with-deps` |
| Env template | `backend/.env.example` documents captcha, proxy, Twilio, iMessage, headless, `WEBHOOK_SECRET` |

## Still not Tsenta-class

| Gap | Reality |
|-----|---------|
| 50k career pages | Hundreds monitored + import/discovery pipeline — not 50k yet |
| Seconds-after-posting | Hot poll **60s** via Celery beat, not webhooks / true push |
| CAPTCHA solve in prod | Client + mock mode wired; real solves need `TWOCAPTCHA_API_KEY`; fills often stop at `needs_user` |
| Auto-submit unattended | **Off by default** (`HEADLESS_APPLY_AUTO_SUBMIT=false`). Enable only with keys + legal sign-off |
| Workday 3–4 step mastery | Adapter exists; listing/account walls still less reliable than Greenhouse/Lever |
| Ashby SPA | Adapter waits for React inputs; less proven than GH/Lever |
| WhatsApp / iMessage | Twilio + bridge adapters; need credentials / Mac host (`TWILIO_*`, `IMESSAGE_BRIDGE_URL`) |
| Proxy evasion | Pool + fingerprints ready; empty without `PROXY_POOL` |
| Hundreds of **successful submits**/user | Packaging + quotas + smoke script; live **submits** not load-tested (we don't spam employers) |

## Tests

```bash
cd backend
python -m pytest tests/test_apply_engine.py tests/test_tsenta_e2e.py \
  tests/test_scale_apply.py tests/test_live_ats_fill.py tests/test_smoke.py -v
```

Live ATS fills require network + Playwright Chromium. Scale smoke (API running):

```bash
python scripts/scale_apply_smoke.py --users 5 --jobs 20
```

## Env for production hardening

```
TWOCAPTCHA_API_KEY=
CAPTCHA_MOCK=false
PROXY_POOL=http://user:pass@host:port,...
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_FROM=whatsapp:+1...
IMESSAGE_BRIDGE_URL=
HEADLESS_APPLY_ENABLED=true
HEADLESS_APPLY_AUTO_SUBMIT=false
WEBHOOK_SECRET=
```

Deploy images need: `playwright install --with-deps chromium` and Celery worker **+ beat**.
