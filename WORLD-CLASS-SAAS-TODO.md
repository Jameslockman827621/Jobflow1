# JobScale World-Class SaaS — Gap TODO (Detailed)

Last updated: 2026-07-16  
Rule: **No mock APIs. No fake success metrics. No silent placeholders that look real.**

This is the product-truth checklist. Items marked **DONE** were closed in this pass. Remaining items stay until proven with real services/fixtures (not stubs).

---

## P0 — Core “Apply for me” loop (user cannot succeed without these)

### P0.1 Job inventory & dashboard load
- [x] **Dashboard always loads matched jobs** — was gated on `has_cached_jobs`, leaving empty dashboards after onboarding (`frontend/.../dashboard/page.tsx`)
- [x] Show error toast when `/onboarding/search` fails (no silent empty)
- [x] Disable `AUTO_SEED_DEMO_JOBS` in production env by default; keep only for empty-dev bootstrap
- [x] Finish ATS `scrape_all_jobs` stubs (Greenhouse/Lever/Ashby/Workable use curated company lists)
- [x] Authenticate + admin-gate `POST /jobs/scrape/{source}` (was open; now auth-required — still needs role/admin)
- [x] Apify LinkedIn company/all scrapes: replace `NotImplementedError` with real actors or remove from API surface

### P0.2 Genuine apply path (not status flips)
- [x] `POST /applications/{id}/submit` no longer pretends it applied — requires `?manual=true` for external self-report, otherwise points to apply-engine
- [x] Headless batch: dashboard **polls** `/apply-engine/headless/batch/{id}` and surfaces submitted / needs_user / connect_hint
- [x] Live LinkedIn/Indeed without Connect → `login_required` + connect hint (prior)
- [x] Celery apply worker documented in QUICKSTART + health `/ready` reports workers
- [ ] Live employer submit smoke (manual, ToS) for Greenhouse + LinkedIn Easy Apply

### P0.3 Connect boards (session)
- [x] Extension cookie sync → BoardSession (prior)
- [x] **Encrypt BoardSession storage_state at rest** (Fernet from SECRET_KEY; plaintext legacy still readable once)
- [x] Extension **configurable API/dashboard base** via `chrome.storage` + options page (not hardcoded forever)
- [x] Production host_permissions for real HTTPS app domains
- [x] Session expiry UI on dashboard when connect status flips to disconnected mid-batch

### P0.4 Quotas & billing honesty
- [x] **Plan-based apply quotas enforced** (free 5/day & 5/month; pro/premium higher) in `apply_limits.py`
- [x] Quota endpoint returns `plan` + monthly remaining
- [x] Stripe webhook handles `customer.subscription.updated` / plan sync (not only checkout + delete)
- [x] Map Stripe Price IDs → plan in env; reject checkout if price IDs missing (already partial)
- [x] Referral credits actually apply Stripe coupon / balance (today cosmetic)

### P0.5 AI that never lies
- [x] CV tailor / cover letter **raise clear error** when `OPENAI_API_KEY` missing (no placeholder letter that looks sendable)
- [x] Interview coach: **real OpenAI** when configured; **503** when not (no random fake scores)
- [x] Wire interview coach UI page OR remove marketing claim on landing (landing claim honesty + API already 503 without key)
- [x] Captcha: refuse genuine submit when neither 2Captcha nor solvable challenge — never accept `mock-captcha-token` in production (`ENVIRONMENT=production`)

---

## P1 — Trust, auth, tracker, analytics (product feels real)

### P1.1 Auth
- [x] `authFetch` clears session + redirects on **401**
- [x] Dead `/api/v1/users/*` placeholder routes return **410 Gone** pointing at `/auth` + `/profile`
- [x] Password reset (token email + set password)
- [x] Email verification endpoints + verify page (`is_verified` on `/me`)
- [x] Refresh tokens / longer-lived sessions for extension
- [x] OAuth (Google) optional

### P1.2 Tracker / Kanban
- [x] Kanban can **move stage** via `PUT /applications/{id}` (select on card)
- [x] Drag-and-drop between columns
- [x] Show apply-run status badge on card (submitted / needs_user / filled)

### P1.3 Analytics & career (no fiction)
- [x] Analytics UI uses **real overview API** (zeros when empty — not 15 apps / 20% interview)
- [x] Funnel built from `by_stage` counts
- [x] Market insights from API (companies/skills) — hide section when empty
- [x] Analytics fake averages removed on backend (`avg_days`, `avg_response`, `acceptance_rate` → computed or null/0)
- [x] Career page: render API analysis, delete static Mid-Level ladder demo
- [x] Reviews page: bind selected company to API detail (kill Stripe hardcode)

### P1.4 Email & notifications
- [x] SendGrid API path when `SENDGRID_API_KEY` set (not “coming soon”)
- [x] Use `APP_URL` for links (not hardcoded localhost in new emails)
- [x] DEBUG still prints — OK for dev; production must not short-circuit if SendGrid/SMTP configured
- [x] Unsubscribe / preference center for alerts

### P1.5 Navigation & honesty
- [x] AppShell includes Career + Reviews
- [x] Landing: remove vaporware claims (recruiter network, expert review) or ship them
- [x] Pricing Premium → real Stripe checkout (not contact-only vaporware)
- [x] Referrals frontend page wired to existing API

---

## P2 — Production hardening

- [x] Global HTTP rate limit middleware (per IP + per user)
- [x] Alembic migrations for **all** tables (stop relying on `create_all` for board_sessions, answer_bank, flags)
- [x] Sentry soft-init via `SENTRY_DSN` (+ `sentry-sdk` dependency); OpenTelemetry soft-init via `OTEL_EXPORTER_OTLP_ENDPOINT`
- [x] Structured logging JSON
- [x] Health check reports: DB, Redis, Celery workers, Playwright package
- [x] Secrets scanning (gitleaks CI + log redaction); never log board cookies
- [x] Extension icons (real 16/48/128 PNG assets, not 1×1)
- [x] CSRF for cookie-based flows if any; tighten CORS in production

---

## P3 — Scale & quality of apply engine

- [x] Workday/Ashby multi-step fixture coverage (genuine submit path); live boards still open
- [x] Answer bank UX in dashboard (CRUD)
- [x] Per-company sticky fingerprint already exists — document + test under concurrency
- [x] Stale run sweeper metrics endpoint for ops
- [x] Company career-page monitor → auto-queue high-match jobs (opt-in)

---

## Acceptance criteria (definition of “world-class E2E”)

1. New user: register → onboard → **sees real matched jobs** (or explicit empty + refresh that re-searches).
2. Create CV → Connect LinkedIn (extension) → select jobs → genuine submit ON → headless queue → dashboard shows **Submitted / Needs action / Connect required** from live poll.
3. Free plan cannot exceed monthly/daily quota (API 429 with reason).
4. Without OpenAI key, tailor/cover/interview endpoints **fail loudly** (no fake content).
5. Without Connect, LinkedIn.com job apply returns connect_hint.
6. Analytics for new account shows **zeros**, not fabricated success.
7. Manual “I applied elsewhere” is explicit (`manual=true`), never confused with JobScale submit.

---

## Implementation log (this pass)

| Area | Change |
|------|--------|
| Limits | Plan-aware quotas |
| Sessions | Fernet encryption |
| AI / Coach | No mock output |
| Submit API | Honest manual vs genuine |
| Dashboard | Jobs always load + batch poll |
| Analytics | Real data only |
| Auth | 401 logout; users 410 |
| Kanban | Stage updates |
| Email | SendGrid |
| Extension | Configurable bases + options |
| Billing | subscription.updated |
| Nav | Career + Reviews |
| Wave 3 | Admin scrape gate; Apify LinkedIn wrappers; rate limit MW; Alembic board/answer/admin; Kanban apply_run badges; reconnect UX; answer-bank CRUD; extension long-lived JWT |
| Wave 4 | Real referral Pro trial + Stripe credit; unsubscribe tokens; interview coach UI; Kanban DnD; prod CORS/email honesty; structlog JSON; ops metrics; extension host_permissions |
| Wave 5 | Monitor auto-queue opt-in; fingerprint concurrency test; cookie/token log redaction; optional SENTRY_DSN hook |
| Wave 6 | Google OAuth (authorize/callback/id_token + login UI); Workday/Ashby multi-step fixtures + submit selectors; real extension icons; gitleaks CI; sentry-sdk in requirements |
| Wave 7 | Extension content/form-filler use chrome.storage bases; OTEL soft-init; billing success polls subscription; checkout URLs use APP_URL; Stripe webhook + Google callback tests; wider CI |
