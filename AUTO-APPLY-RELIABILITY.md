# Auto-Apply Reliability Report

Last hardened: 2026-07-17 (world-class plan + W0–W5)  
Master plan: `WORLD-CLASS-AUTO-APPLY-PLAN.md`  
Metrics suite: `tests/test_world_class_auto_apply_metrics.py` — **17 passed**

Rule: **Never claim live Easy Apply success without Connect + Celery + ToS-aware smoke.**

## Can we say “applies for all your jobs every time”?

**No — not for arbitrary live employer sites.** That claim is false for any apply product.

**What we can say with evidence:**

> With genuine submit opted in, Celery workers running, and LinkedIn/Indeed Connected when needed, JobScale’s headless engine **reliably submits** on supported ATS fixture flows (Greenhouse, Lever, Ashby, Workday, Workable, SmartRecruiters, iCIMS, Indeed Apply) and **fails closed** on every automated edge metric in A–E (+ F1/F2 fixtures).

## World-class waves shipped

| Wave | Highlights |
|------|------------|
| 1–2 | Batch meta, confirmation honesty, quotas, heartbeats, login walls |
| W1 | Concurrency lock, board_key, extension report gate, screenshots |
| W2 | Dashboard reconnect/retry/extension-missing UX |
| W3 | Captcha wall + uncertain confirm (no URL-only fake submit) |
| W4 | Batch session preflight warnings |
| W5 | SmartRecruiters + iCIMS adapters + fixtures |

## Still open

Taleo/SuccessFactors, durable S3 screenshots, Turnstile/Arkose, live ToS smoke, monitor→headless drain.

## How to re-run

```bash
cd backend
./venv/bin/python -m pytest \
  tests/test_world_class_auto_apply_metrics.py \
  tests/test_auto_apply_edge_matrix.py \
  -q --tb=line
```
