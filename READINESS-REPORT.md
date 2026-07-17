# JobScale User Readiness Report

Generated: `2026-07-16T15:25Z` (UTC)  
Environment: local Docker Postgres + Redis, API `:8000`, Next.js `:3000`  
Branch: `cursor/tsenta-gap-closure-e2e-24ca`

## Verdict

**Core user loop is ready for staged demo / dogfood** with secrets + Celery workers configured.  
**Not production-ready** for unattended genuine Easy Apply at scale until Celery/beat, Stripe, OpenAI (optional), Google OAuth client, Connect cookies, and live ToS smokes are in place.

| Layer | Result | Proof |
|-------|--------|-------|
| Backend pytest | **102 passed**, 0 failed, 2 deselected (`live_ats*`) | `/opt/cursor/artifacts/pytest-junit.xml`, log `pytest-full.log` |
| Live API journey probe | **85/88** (96.6%) after bugfixes | `/opt/cursor/artifacts/readiness-full.json` |
| Frontend HTTP routes | **22/22 → 200** after installing missing `sonner` | curl matrix below |
| Extension static integrity | **PASS** (assets + chrome.storage bases) | probe `extension::*` |
| OpenAPI surface | **125 paths** | `GET /openapi.json` |

---

## What works (proven)

### Auth & session
- Register → Login → `/auth/me` → extension JWT — **PASS**
- Forgot-password accepts request — **PASS**
- Legacy `/users/me` returns **410** (honest deprecation) — **PASS**
- Google OAuth start returns **503** when unset (honest) — **PASS**

### Onboarding → jobs → applications
- Save preferences → search → list matched jobs — **PASS**
- `GET /jobs/` lists jobs (after fix for null `location`) — **PASS** (50 jobs in probe sample)
- Scrape endpoint admin-gated (**403** for normal user) — **PASS**
- Start application, list apps, Kanban stage `PUT` — **PASS**
- Submit without `manual=true` rejected (**400**, honest) — **PASS**
- Submit with `?manual=true` — **PASS**
- Headless **dry_run** returns structured result — **PASS**

### Apply engine / Connect
- Connect status, quota (plan-aware), settings patch — **PASS**
- Empty LinkedIn cookies rejected (**400**) — **PASS**
- Answer-bank CRUD — **PASS**

### Product APIs
- Analytics overview — **PASS**
- Career analysis + paths — **PASS** (after null `years_of_experience` fix)
- Reviews companies — **PASS**
- Auto-apply jobs list, companies list, referral **code** — **PASS**
- Interview coach **503** without OpenAI (honest) — **PASS**
- Billing subscription (free), checkout **503** without Stripe, webhook **503** without secret — **PASS**

### Frontend pages (HTTP 200 after `sonner` install)
`/`, `/login`, `/pricing`, `/dashboard`, `/onboarding`, `/kanban`, `/analytics`, `/career`, `/reviews`, `/profile`, `/referrals`, `/answers`, `/alerts`, `/cv-builder`, `/interview-coach`, `/forgot-password`, `/billing/success`, `/unsubscribe`, `/verify-email`, `/privacy`, `/terms`, `/contact`

### Extension
- Manifest, background/content/form-filler/popup/options present
- Icons real (128px > 100 bytes)
- form-filler/`content.js` read `api_base` / `dashboard_url` from `chrome.storage`

### Honesty checks
- Pricing no longer claims “Unlimited applications”
- Pricing documents Pro **500/month**
- FAQ states we do **not** advertise money-back guarantee

### Automated regression (pytest)
Includes waves 3–5, Google OAuth, billing webhooks, Workday/Ashby/Greenhouse fixtures, connect boards E2E, scale reliability, world-class honesty, Alembic baseline, etc. — **102 green**.

---

## What does not work / not ready (proven)

### Blockers for unattended production apply
| Gap | Evidence | Impact |
|-----|----------|--------|
| **Celery workers down** | `/health/ready` → `celery_workers.ok=false` | Headless batch queue / async apply will not run |
| **Celery beat not observed** | ops_hint requires beat for stale-run sweeper | ApplyRuns can stick in `running` |
| **No live board cookies** | Connect exercised only with empty-cookie rejection | LinkedIn/Indeed Easy Apply cannot succeed without Connect |
| **Live employer ToS smoke not run** | `test_live_ats*` deselected; prior hang on Playwright live nav | Cannot claim live Greenhouse/LinkedIn submit works in this env |
| **No Stripe / Google OAuth / 2Captcha / OpenAI secrets** | Honest 503s on checkout, Google start, coach; captcha_available=false | Paid billing, OAuth login, captcha solve, AI tailor/coach unavailable until configured |

### Product / API gaps found in probe
| Gap | Evidence | Severity |
|-----|----------|----------|
| Inbound messaging webhook path not found at probed URLs | `POST /webhooks/inbound` → **404** | Info — route naming mismatch vs probe guesses (OpenAPI has webhook routes under other paths) |
| `/api/v1/referrals/` and `/referrals/me` **404** | Use `/referrals/code`, `/stats`, `/claim` instead | Info — frontend must hit correct paths |
| `/api/v1/alerts/` **404** | Settings may live under salary-alerts alternate paths | Info |
| `/companies/monitored` **404** | List via `/companies/` works | Info |

### Bugs found & fixed during this readiness pass
| Bug | Before | After |
|-----|--------|-------|
| `GET /jobs/` ResponseValidationError on null `location` | **HTTP 500** | **200** (`JobResponse.location` Optional) |
| `GET /career/analysis` TypeError on null years | **HTTP 500** | **200** (coerce years to 0) |
| Frontend pages importing `sonner` without dependency | **HTTP 500** Module not found | **200** after `npm install sonner` |

### Frontend typecheck (still dirty)
`npx tsc --noEmit` reports implicit `any` in `analytics/page.tsx` and previously sonner missing (resolved). Lint: multiple `react-hooks/exhaustive-deps` warnings — non-blocking.

---

## User journey scorecard

| Journey | Status | Notes |
|---------|--------|-------|
| Sign up / log in | ✅ | Proven live |
| Complete profile + prefs | ✅ | Proven live |
| Search & see jobs | ✅ | Proven live |
| Create CV | ✅ | Proven live |
| Track application + Kanban stage | ✅ | Proven live |
| Manual “I applied” | ✅ | `?manual=true` |
| Genuine headless submit (fixture) | ✅ via pytest | Workday/Ashby/Greenhouse fixtures |
| Genuine Easy Apply (LinkedIn live) | ❌ not proven | Needs Connect + Celery + ToS smoke |
| Pay for Pro | ❌ env | Needs Stripe keys (honest 503 now) |
| Google login | ❌ env | Needs OAuth client (honest 503 now) |
| AI tailor / interview coach | ❌ env | Needs OpenAI (honest 503/422) |
| Extension Connect in Chrome | ⚠️ static only | Code paths OK; not browser-automated here |

---

## Artifacts

- `/opt/cursor/artifacts/READINESS-REPORT.md` (this report)
- `/opt/cursor/artifacts/readiness-full.json` — per-check probe results
- `/opt/cursor/artifacts/pytest-junit.xml` — 102 passed
- `/opt/cursor/artifacts/pytest-full.log`
- `/opt/cursor/artifacts/probe-final.log`
- `/workspace/READINESS-REPORT.md` + `READINESS-REPORT-API.json`
- Probe scripts: `backend/scripts/readiness_probe_v2.py`

---

## Recommended next steps to go from “demo ready” → “production ready”

1. Run Celery worker + beat; confirm `/health/ready` celery_workers.ok
2. Configure Stripe price IDs + webhook; Google OAuth client; optional OpenAI / 2Captcha
3. Manual Connect LinkedIn (extension) → one real Easy Apply under ToS policy
4. Fix remaining TS `any` in analytics; keep `sonner` in lockfile
5. Align frontend referral/alerts URLs with actual API paths (avoid 404s)
