# Tsenta Gap Closure — Honest Status (final matrix)

## Verified working (not scaffolding)

| Capability | Evidence |
|------------|----------|
| Account register/login/me | Live API + pytest |
| Greenhouse **live form fill** | Playwright filled real GitLab board; `core_ok=true` |
| Lever **live form fill** | Playwright filled Wealthfront `/apply`; pytest green |
| **Genuine submit (fixture)** | Fill → Submit → “Thank you” confirmation; `status=submitted` (`test_genuine_auto_apply`, `test_world_class_apply`) |
| **Multi-step genuine submit** | Greenhouse-like 2-step fixture advances Next then submits with confirmation |
| User opt-in gate | `User.auto_apply_submit` + platform kill-switch; without opt-in, never submits |
| Profile completeness gate | Hard-blocks genuine submit when name/email/resume missing |
| Real PDF resumes | Minimal valid `%PDF-` generated; `GET /api/v1/cvs/{id}/pdf` |
| Shared CAPTCHA helper | All adapters call `detect_and_solve_captcha` before gated submit |
| Confirmation-strict submit | URL change alone ≠ submitted; requires thank-you / confirmation pattern |
| Headless batch fan-out | `apply_batch` queues one Celery task per application |
| Retry failed applies | `POST /apply-engine/headless/retry` re-queues `failed` / `needs_user` |
| Extension genuine path | Resume PDF attach + Next-only multi-step + optional submit + `status=submitted` report |
| Dashboard Automation panel | “Genuinely submit for me” opt-in + headless queue |
| Company discovery / coverage | Monitored boards + coverage API |
| Health `/ready` | DB hard check; Redis degraded-ok; captcha / proxy / messaging flags |
| **Scale: apply queue** | Dedicated Celery `apply` queue, `--concurrency=1` apply-worker, fan-out + rate limit |
| **Scale: quotas** | Billable statuses only; enforced inside `apply_one`; failed/dry_run don't burn quota |
| **Scale: stale sweeper** | Beat marks `running` >15m as `stale` every 5 minutes |
| **Scale: observability** | `GET /headless/batch/{batch_id}`, `GET /metrics/apply`, `batch_id` on runs |
| **Workable adapter** | Dedicated fill/submit (not Generic); fixture genuine submit proven |
| **Answer bank** | Persisted Q→A; `/answer` upserts; reused across applications |
| **Sticky fingerprints** | UA/platform stable per `user_id` (matches sticky proxy) |
| **Validation recovery** | One refill loop on Next/Submit validation errors before `needs_user` |
| **Idempotent submit** | Already-`submitted` applications skip re-apply |

## Still not Tsenta-class

| Gap | Reality |
|-----|---------|
| 50k career pages | ~1k seed catalog + discovery — not 50k yet |
| Seconds-after-posting | Hot poll **60s** via Celery beat, not true push |
| CAPTCHA solve in prod | Wired for all adapters; real boards need `TWOCAPTCHA_API_KEY` (mock won’t pass employers) |
| Live employer auto-submit | Proven on fixtures; **not** load-tested against real boards (don’t spam) |
| Workday account walls | Guest / Apply Manually heuristics improved; many boards still need user login |
| LinkedIn / Indeed live | Adapters + session API + fixtures proven; live Easy Apply needs `storage_state` upload |
| Company sites | Generic + ATS handoff; quirky custom forms may still need the user |
| WhatsApp / iMessage | Twilio + bridge adapters; need credentials |
| Proxy evasion | Pool ready; empty without `PROXY_POOL` |
| Hundreds of successful submits/user | Quotas + fan-out ready; measure after keys + worker deploy |

## How genuine auto-apply works

1. User enables **Genuinely submit for me** (sets `auto_apply_submit=true`)
2. Profile needs name, email, resume (phone recommended)
3. Queue headless with `auto_submit=true` (dashboard or `POST /apply-engine/headless/batch`)
4. Celery worker runs Playwright → fill → solve CAPTCHA if keyed → submit → confirmation
5. Application marked `submitted` only when confirmation detected
6. Retry stuck runs via `POST /apply-engine/headless/retry`

## Tests

```bash
cd backend
./venv/bin/pytest tests/test_genuine_auto_apply.py tests/test_world_class_apply.py -v
```

Broader suite:

```bash
./venv/bin/pytest tests/test_apply_engine.py tests/test_tsenta_e2e.py \
  tests/test_scale_apply.py tests/test_live_ats_fill.py tests/test_smoke.py -v
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
HEADLESS_APPLY_AUTO_SUBMIT=true
WEBHOOK_SECRET=
```

Deploy images need: `playwright install --with-deps chromium` and Celery worker **+ beat**.
User must still opt in via dashboard; platform kill-switch alone is not enough.
