# Tsenta Gap Closure — Implementation Status

Audit of JobScale vs world-class (Tsenta-class) apply automation, and what shipped in this branch.

| Gap | Before | After (this PR) |
|-----|--------|-----------------|
| Company coverage | ~52 Greenhouse constants | **382 seeded career pages** across Greenhouse/Lever/Workable/Ashby/custom + DB `MonitoredCompany` + bulk import toward **50k capacity** |
| Monitoring frequency | Every 6h (Beat often not running) | **Hot 60s / warm 15m / cold 2h** + Celery Beat service in docker-compose |
| Form filling | None (open tab only) | Extension `form-filler.js`: text, select, radio, checkbox, textarea, file hooks, open-ended answers |
| CAPTCHA | None | **2Captcha** client + `/apply-engine/captcha/solve` + extension injection |
| Bot evasion | UA only | **Proxy pool rotation** + fingerprint headers (Playwright + scrapers) |
| Multi-step forms | None | Multi-step walker (Workday up to 6 steps) in extension + headless |
| Mobile/iMessage | None | **WhatsApp (Twilio)** + **iMessage bridge** adapter + bot commands |
| Server-side apply | Browser must stay open | **Playwright headless apply** + Celery batch queue |
| Scale testing | 1 user / ~50 jobs | Batch headless API (up to 200) + E2E tests covering account → package → dry-run |

## Key APIs

- `POST /api/v1/companies/seed` — seed monitored directory
- `GET /api/v1/companies/coverage` — coverage metrics
- `POST /api/v1/companies/import` — bulk import (scale to 50k)
- `GET /api/v1/apply-engine/package/application/{id}` — fill plan for extension/headless
- `POST /api/v1/apply-engine/answer` — open-ended answers
- `POST /api/v1/apply-engine/headless` — unattended apply (`dry_run` supported)
- `POST /api/v1/apply-engine/headless/batch` — scale queue
- `POST /api/v1/apply-engine/messaging/inbound` — WhatsApp/iMessage bot commands

## Env vars

```
TWOCAPTCHA_API_KEY=
PROXY_POOL=http://user:pass@host:port,...
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_FROM=whatsapp:+1...
IMESSAGE_BRIDGE_URL=https://your-mac-bridge
HEADLESS_APPLY_ENABLED=true
```

## Tests

```bash
cd backend && python -m pytest tests/test_apply_engine.py tests/test_tsenta_e2e.py -v
```

Account flow verified: register → login → `/auth/me` → company seed/coverage → apply package → headless dry-run → messaging HELP.
