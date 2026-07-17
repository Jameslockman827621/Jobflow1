# World-Class Auto-Apply — Master Plan & Pass Metrics

**Date:** 2026-07-17  
**Branch:** `cursor/world-class-auto-apply-24ca`  
**Rule:** Never claim live Easy Apply success without Connect + Celery + ToS-aware smoke.  
**Bar:** Fail closed always. Confirm before `submitted`. Recover or explain every failure.

---

## What “world-class” means (research + audit)

Competitors that actually submit (Tsenta / FastApply class) win on:

1. **Per-ATS submission adapters** (not one generic filler) — Workday review page, Greenhouse modal, Lever verify, Easy Apply wizards
2. **Confirmation from the ATS page** — not a bot “queued” email
3. **Session authenticity** — real browser cookies / residential context for LI/Indeed
4. **Rate discipline** — volume anomaly detection on Workday/Greenhouse punishes spam
5. **Honest UX** — reconnect, retry, per-run errors, never silent fake success
6. **Ops** — heartbeats, stale reclaim, screenshots, idempotency, concurrency locks

JobScale today is honesty-oriented and fixture-proven on GH/Lever/Ashby/Workday/Workable/Indeed. Gaps vs world-class: races, extension trust, board reconnect UX bugs, thin retries, ephemeral artifacts, missing enterprise ATS adapters, no continuous live-submit CI.

---

## Product reliability contract (non-negotiable)

```
GENUINE SUBMIT only if:
  request.auto_submit AND user.auto_apply_submit AND HEADLESS_APPLY_AUTO_SUBMIT
  AND profile hard-complete AND adapter readiness AND confirmation detected

ELSE:
  needs_user | filled | failed | stale | deferred — NEVER fake submitted

LinkedIn.com / Indeed.com without valid BoardSession:
  needs_user + connect_hint + board_key — NEVER empty-browser “success”

BoardSession present + login wall:
  invalidate session + needs_reconnect + board_key

Concurrent apply on same application_id:
  second run skipped (already_running) — NEVER double-submit

Extension POST /report status=submitted without confirmation_detected:
  coerce to needs_user (submit_unconfirmed_extension) — NEVER trust client alone
```

---

## Pass metric matrix

Legend: **PASS** = automated test green · **MANUAL** = ToS smoke · **DEFERRED** = documented stretch

### A. Honesty & submit gates

| ID | Edge case | Pass metric | Suite |
|----|-----------|-------------|-------|
| A1 | Opt-in off | `submitted!=true`, `genuine_apply!=true` | edge_matrix |
| A2 | Dry-run | never `submitted` | edge_matrix |
| A3 | Platform kill-switch off | no genuine submit | metrics |
| A4 | Profile missing email/name/resume-on-page | `profile_incomplete` / resume gate | metrics |
| A5 | Weak “applied” text | confirmation false | edge_matrix |
| A6 | Strong thank-you | confirmation true | edge_matrix |
| A7 | Clicked submit, no confirm | `submit_unconfirmed`, not submitted | metrics |
| A8 | Extension report submitted w/o proof | coerced off submitted | metrics |
| A9 | Manual apps submit without `?manual=true` | 400 genuine_submit_required | honesty |

### B. Board Connect / sessions

| ID | Edge case | Pass metric | Suite |
|----|-----------|-------------|-------|
| B1 | Live LI URL, no session | `login_required` + connect_hint | edge_matrix |
| B2 | Live Indeed URL, no session | same | edge_matrix |
| B3 | Login wall + session | `session_invalidated`, is_valid=0 | edge_matrix |
| B4 | Batch meta exposes `board_key` | `linkedin`\|`indeed` string for reconnect | metrics |
| B5 | Cookie missing `li_at` | Connect API 400 | connect_e2e |
| B6 | Session tempfile | mode 0o600 + deleted after run | metrics |

### C. ATS fixture genuine submit

| ID | Edge case | Pass metric | Suite |
|----|-----------|-------------|-------|
| C1–C6 | GH / Workday / Ashby / Lever / Workable / Indeed Apply | `submitted=true` with opt-in | edge_matrix |
| C7 | Indeed email field ≠ login wall | submit succeeds | edge_matrix |
| C8 | Indeed login wall | `login_required` | edge_matrix |
| C9 | LI Easy Apply fixture | submit or fail-closed | board_coverage |
| C10 | Company site → ATS handoff | submitted | board_coverage |
| C11 | Fill-only | needs_user, not submitted | edge_matrix |
| C12 | Captcha present, no solver | needs_user, captcha blocked | metrics |
| C13 | Validation error then refill | advances or needs_user (not fake submit) | metrics |

### D. Scale / concurrency / ops

| ID | Edge case | Pass metric | Suite |
|----|-----------|-------------|-------|
| D1 | Two concurrent headless on same app | exactly one submit attempt; other `already_running` | metrics |
| D2 | Already submitted app | skipped idempotent | metrics |
| D3 | Quota free 5/day | 6th blocked; login_required not billed | edge_matrix |
| D4 | Stale sweeper + recent heartbeat | alive spared, dead stale | edge_matrix |
| D5 | Batch fan-out | Celery apply_async per id | scale |
| D6 | needs_user/submit_uncertain screenshot | `screenshot_path` in meta | metrics |
| D7 | Progress heartbeat written | `last_progress_at` during run | metrics |

### E. Dashboard / extension UX

| ID | Edge case | Pass metric | Suite |
|----|-----------|-------------|-------|
| E1 | Reconnect uses `board_key` / `needs_reconnect` | Indeed failure → Indeed CTA (not LinkedIn) | metrics + FE |
| E2 | Retry after reconnect | `POST /headless/retry` wired in UI | FE + API test |
| E3 | Extension missing on Connect | error toast + install hint (not silent) | FE |
| E4 | Batch done with needs_user | toast not pure “success” | FE |
| E5 | Dual path clarity | popup labeled autofill; dashboard = genuine queue | FE copy |

### F. Stretch (enterprise / live) — plan now, ship iteratively

| ID | Edge case | Pass metric | Status |
|----|-----------|-------------|--------|
| F1 | SmartRecruiters adapter + fixture | C-class submit | **PASS** (fixture 2026-07-17) |
| F2 | iCIMS adapter + fixture | C-class submit | **PASS** (fixture 2026-07-17) |
| F3 | Taleo / SuccessFactors | C-class or honest generic fail | DEFERRED |
| F4 | Live ToS smoke LI Easy Apply | manual checklist | MANUAL |
| F5 | Durable screenshot storage (S3) | not /tmp only | DEFERRED |
| F6 | Turnstile / Arkose captcha | blocked_reason or solve | DEFERRED |
| F7 | Monitor list → scheduled headless drain | opt-in only | DEFERRED |

---

## Execution waves (keep going until A–E PASS)

| Wave | Scope | Exit criteria |
|------|-------|---------------|
| **W0** | This plan + metrics harness | Doc merged; `test_world_class_auto_apply_metrics.py` exists |
| **W1** | Concurrency lock, board_key in batch, extension report honesty, screenshots on needs_user, already_running | A8, B4, D1, D2, D6 green |
| **W2** | Dashboard reconnect/retry/extension missing/toast honesty | E1–E5 green (lint + targeted tests) |
| **W3** | Captcha-block fixture, uncertain-submit fixture, platform kill-switch test | A3, A7, C12 green |
| **W4** | Session preflight on batch for LI/Indeed | B-class warning in API + test |
| **W5+** | F-tier ATS adapters one-by-one | each F* → C-class |

**Stop condition:** All A–E automated metrics PASS. F1–F2 fixture PASS. Remaining F* tracked openly, not pretended done.

### Wave status (2026-07-17)

| Wave | Status |
|------|--------|
| W0 Plan + metrics harness | DONE |
| W1 Concurrency, board_key, extension honesty, screenshots | DONE — metrics green |
| W2 Dashboard reconnect/retry/extension UX | DONE |
| W3 Captcha + uncertain confirm + kill-switch | DONE |
| W4 Batch session preflight | DONE |
| W5 SmartRecruiters + iCIMS adapters | DONE (fixture) |
| W6+ Taleo/SuccessFactors, S3 artifacts, live ToS | OPEN |

---

## How to verify

```bash
cd backend
./venv/bin/python -m pytest \
  tests/test_world_class_auto_apply_metrics.py \
  tests/test_auto_apply_edge_matrix.py \
  tests/test_connect_boards_e2e.py \
  tests/test_scale_reliability.py \
  -q --tb=line
```

Update this file’s checklist as metrics go green. Never mark MANUAL/DEFERRED as PASS without evidence.
