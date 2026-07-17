# World-Class Board Coverage Checklist

LinkedIn Easy Apply · Indeed · Company career sites · ATS handoff

Status: **IN PROGRESS** — checkboxes track implementation in this branch.

---

## 0. Classification & routing

- [x] Detect LinkedIn / Indeed / Greenhouse / Lever / Ashby / Workday / Workable / generic from URL
- [x] Classify apply mode: `easy_apply` | `external_redirect` | `ats_direct` | `company_site` | `login_required`
- [x] Route headless to dedicated adapters (not silent Generic for LinkedIn/Indeed)
- [x] On external redirect, detect destination ATS and **hand off** to that adapter
- [x] Persist `apply_mode` + `handoff_ats` on ApplyRun meta

## 1. Login / session (LinkedIn & Indeed)

- [x] `BoardSession` model (user_id, board, encrypted/storage_state JSON, expires)
- [x] API: `GET/PUT/DELETE /apply-engine/board-sessions/{board}`
- [x] Headless Playwright loads `storage_state` when present
- [x] Detect logged-out wall → `needs_user` + `blocked_reason=login_required`
- [x] Extension can report session present / missing (via package capabilities)
- [ ] Production: OAuth / cookie import UI in dashboard (API ready; UI polish later)
- [ ] Production: refresh/validate session health ping

## 2. LinkedIn Easy Apply

- [x] `LinkedInAdapter` registered in `get_adapter`
- [x] Open job → click **Easy Apply** (not “Apply on company website” when Easy Apply exists)
- [x] Multi-step modal: Next / Review / Submit
- [x] Fill contact, phone, email, resume upload
- [x] Answer custom questions (heuristics + answer bank)
- [x] Confirmation detection (“Application sent”, “applied”)
- [x] External apply button → handoff classification (do not fake-submit)
- [x] Fixture HTML + genuine submit test
- [x] Extension `fillLinkedIn` path
- [ ] Live Easy Apply against real LinkedIn (needs user session + legal/ToS review)
- [ ] Handle “Already applied” / daily Easy Apply limits

## 3. Indeed Apply

- [x] `IndeedAdapter` registered in `get_adapter`
- [x] Indeed Apply / Easy Apply modal flow
- [x] Resume + contact fill
- [x] Multi-step Continue / Submit
- [x] “Apply on company site” → capture external URL → handoff
- [x] Login wall → `needs_user`
- [x] Fixture HTML + genuine submit + redirect handoff tests
- [x] Extension `fillIndeed` path
- [ ] Live Indeed Apply (needs session)
- [ ] Indeed email verification / CAPTCHA paths

## 4. Generic / company career sites

- [x] Stronger `GenericAdapter`: label strategies, file upload, Next loop, validation recovery
- [x] Detect embedded Greenhouse/Lever/Ashby/Workday iframes or links → handoff
- [x] “Apply” CTA discovery beyond first button
- [x] Confirmation patterns shared with submit helper
- [x] Fixture company-site + iframe/link handoff to Greenhouse fixture
- [x] Extension generic pass already fills by alias; improve Next-only + submit
- [ ] Visual/DOM ML field mapping (future)
- [ ] Per-company selector overrides table (future)

## 5. ATS handoff engine

- [x] `board_classify.py` — classify URL + extract external apply URL from page
- [x] `handoff.py` — after redirect, re-detect ATS and run target adapter.fill
- [x] Headless wires handoff when adapter returns `meta.handoff_url` / `apply_mode=external_redirect`
- [x] Meta records `handoff_from`, `handoff_to`, `handoff_ok`
- [ ] Cross-domain cookie isolation documentation for ops

## 6. Extension parity

- [x] `fillLinkedIn` / `fillIndeed` in form-filler.js
- [x] Easy Apply button click + multi-step in extension
- [x] Report `submitted` / `needs_user` / `external_redirect` statuses
- [x] Popup sets pending application for autofill (prior work)
- [ ] Chrome identity / cookie sync for LinkedIn/Indeed (manual session upload via API for now)

## 7. Reliability & scale

- [x] Same submit gates: user opt-in, confirmation-strict, captcha, profile completeness
- [x] Quota / fan-out / stale sweeper apply unchanged
- [x] Structured `blocked_reason`: `login_required`, `external_redirect`, `easy_apply_unavailable`, `already_applied`
- [ ] Per-board rate limits (LinkedIn daily Easy Apply cap)

## 8. Tests & proof

- [x] LinkedIn Easy Apply fixture → submitted
- [x] Indeed Apply fixture → submitted
- [x] Indeed external redirect → handoff to Greenhouse fixture → submitted
- [x] Company site generic → submitted
- [x] Login wall → needs_user + login_required
- [x] Classification unit tests
- [ ] Live smoke (manual, session required)

## 9. Docs / ops

- [x] This checklist
- [x] `.env.example` notes for board sessions
- [x] QUICKSTART / TSENTA gap note for LinkedIn/Indeed

---

## How to use (after session upload)

1. Export cookies / Playwright `storage_state` for LinkedIn or Indeed (logged-in browser)
2. `PUT /api/v1/apply-engine/board-sessions/linkedin` with `{ "storage_state": {...} }`
3. Enable **Genuinely submit for me**
4. Queue headless apply on a LinkedIn/Indeed job URL
5. Watch `ApplyRun.meta` for `apply_mode`, `handoff_*`, `blocked_reason`
