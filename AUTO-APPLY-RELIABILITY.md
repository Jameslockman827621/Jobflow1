# Auto-Apply Reliability Report

Last hardened: 2026-07-17 (wave 2)  
Rule: **Never claim live Easy Apply success without Connect + Celery + ToS-aware smoke.**

## Can we say “applies for all your jobs every time”?

**No — not for arbitrary live employer sites.** That claim is false for any apply product.

**What we can say with evidence:**

> With genuine submit opted in, Celery workers running, and LinkedIn/Indeed Connected when needed, JobScale’s headless engine **reliably submits** on supported ATS fixture flows (Greenhouse, Lever, Ashby, Workday, Workable, Indeed Apply) and **fails closed** (needs_user / connect_hint / no fake submitted) on every edge case we automated.

## Hardenings — wave 1

| Fix | Why |
|-----|-----|
| Batch status returns `meta` (`blocked_reason`, `connect_hint`, `session_invalidated`) + `needs_reconnect` | Dashboard reconnect UX was blind |
| Batch lookup uses SQL `LIKE` on `batch_id` (not “last 500 runs”) | High-volume users missed batch completion |
| LinkedIn confirmation no longer treats bare `"applied"` as success | False submit on Easy Apply review pages |
| Quota excludes `login_required` / `profile_incomplete` / Workday account wall | Connect failures burned free-tier quota |
| Resume hard-gate when page has file input and CV file was not attached | Submit without resume |
| Board session temp files `chmod 600` + deleted in `finally` | Cookie leak on disk |
| Lever HTML fixture + edge matrix suite | Lever had no E2E parity |

## Hardenings — wave 2

| Fix | Why |
|-----|-----|
| Indeed login wall uses strong signals only (`#login-email-input`, “Sign in to Indeed”) | Bare `input[name=email]` on apply forms was false-positive login_required |
| Captcha detect returns immediately when no iframe/sitekey markers | Removed multi-second wait tax on every apply |
| Submit confirm re-poll (2s) after uncertain click | SPA late-paint confirmations were marked submit_unconfirmed |
| `_touch_run_progress` heartbeats during navigate/fill | Stale sweeper killed long-but-alive applies |
| `fail_stale_apply_runs` prefers `meta.last_progress_at` | Same — progress-aware timeout (default 30m) |
| Login wall with Connect session → `is_valid=0` + reconnect | Expired cookies left “connected” UI lying |
| Workable + Indeed Apply fixtures in edge matrix | Parity gaps vs Greenhouse/Lever/Ashby/Workday |
| LinkedIn/Indeed login detection: no mixed CSS+`text=/…/` selectors | Playwright threw → silent `False` → missed login walls |

## Edge-case matrix (proven)

Suite: `backend/tests/test_auto_apply_edge_matrix.py` — **19 collected** (verified 2026-07-17).

| Case | Result |
|------|--------|
| Opt-in required for genuine submit | PASS — no silent submit |
| Dry-run never submits | PASS |
| Greenhouse / Workday / Ashby / Lever / Workable / Indeed Apply genuine submit | PASS |
| Indeed apply form email input is NOT login wall | PASS |
| Indeed login wall fixture → needs_user | PASS |
| Fill-only → needs_user (no submit) | PASS |
| Weak page text `"applied"` is NOT confirmation | PASS |
| Strong “thank you for applying” IS confirmation | PASS |
| `login_required` runs do not burn quota | PASS |
| 5× `submitted` burns free daily quota | PASS |
| Batch status exposes meta + needs_reconnect | PASS |
| Live LinkedIn.com / Indeed.com without Connect → connect_hint | PASS |
| Login wall invalidates BoardSession | PASS |
| Stale sweeper spares runs with recent `last_progress_at` | PASS |

## Reliability contract (product truth)

```
IF job is Greenhouse / Lever / Ashby / Workday / Workable (direct ATS URL)
AND user.auto_apply_submit = true
AND platform HEADLESS_APPLY_AUTO_SUBMIT = true
AND Celery worker on queue `apply` is running
AND profile has name + email (+ resume when form asks)
THEN headless apply MUST either:
  • status=submitted with confirmation pattern, OR
  • status=needs_user with blocked_reason (never fake submitted)

IF job is LinkedIn.com / Indeed.com
AND BoardSession missing/invalid
THEN status=needs_user + connect_hint (never launch empty browser as success)

IF BoardSession present but page is a login wall
THEN invalidate session + needs_user + connect_hint

IF confirmation uncertain after click
THEN re-poll once; still uncertain → needs_user + submit_unconfirmed (never mark submitted)

IF apply run is running but last_progress_at older than stale threshold
THEN mark stale (alive heartbeats are spared)
```

## Still required for production “apply for you”

1. **Celery worker + beat** — `/health/ready` must show workers; beat clears stale `running` runs  
2. **Connect** LinkedIn/Indeed via extension before Easy Apply  
3. **Manual ToS smoke** on a real employer board (not automated here)  
4. Optional: 2Captcha for captcha-gated boards  

Without (1)–(3), the product correctly refuses or queues — it does **not** pretend it applied.

## How to re-run

```bash
cd backend
./venv/bin/python -m pytest \
  tests/test_auto_apply_edge_matrix.py \
  tests/test_scale_reliability.py::test_fail_stale_apply_runs \
  -q --tb=line
```
