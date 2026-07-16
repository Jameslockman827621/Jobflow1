# Connect LinkedIn / Indeed → Auto-Apply E2E Checklist

Goal: user clicks **Connect LinkedIn** (or Indeed), logs in once, JobScale syncs the session, then headless Easy Apply works end-to-end.

> Note: LinkedIn does not offer an OAuth scope that performs Easy Apply. Real automation uses the user’s logged-in browser session (extension cookie sync → Playwright `storage_state`). That *is* the product “connect” path.

---

## 1. Product flow

- [x] Dashboard shows Connect LinkedIn / Connect Indeed with status
- [x] Click Connect → opens board login/feed + asks extension to sync
- [x] Extension reads cookies (`li_at`, Indeed session) via `chrome.cookies`
- [x] Extension POSTs cookies → backend stores as `BoardSession` / Playwright `storage_state`
- [x] Dashboard polls connect status until Connected
- [x] Disconnect clears session
- [x] Genuine submit + headless apply uses saved session automatically
- [x] Missing session → clear `login_required` / connect prompt (not silent fail)

## 2. Backend

- [x] `GET /apply-engine/connect/status` — linkedin/indeed connected, last_used, cookie_hint
- [x] `POST /apply-engine/board-sessions/{board}/from-cookies` — Chrome cookie array → storage_state
- [x] Validate required cookies (`li_at` for LinkedIn; Indeed session cookies)
- [x] Existing PUT/GET/DELETE board-sessions remain
- [x] Package capabilities expose `board_session` + `needs_session`

## 3. Extension

- [x] `cookies` permission in manifest
- [x] Content scripts on `linkedin.com/*` and `indeed.com/*` (not only /jobs)
- [x] `syncBoardSession(board)` in background service worker
- [x] Auto-sync when user is on LinkedIn/Indeed while logged into JobScale
- [x] Popup: Connect LinkedIn / Connect Indeed buttons + status
- [x] Dashboard bridge: `jobscale-connect-board` custom event → background sync

## 4. Dashboard UX

- [x] Connected / Not connected badges
- [x] Connect buttons with short instructions
- [x] Disconnect
- [x] Copy that extension must be installed

## 5. Apply path

- [x] Headless loads `storage_state` for linkedin/indeed (prior work)
- [x] Login wall → `needs_user` + blocked_reason `login_required`
- [x] With session + fixture/live Easy Apply → submit when opted in

## 6. Tests

- [x] Cookie → storage_state conversion unit/API test
- [x] Connect status API
- [x] from-cookies rejects missing `li_at`
- [x] Headless apply with injected BoardSession on LinkedIn fixture → submitted
- [ ] Live LinkedIn Easy Apply (manual; needs real account + ToS acceptance)

## 7. Ops / honesty

- [x] Document: Connect = extension session sync, not LinkedIn OAuth API
- [x] Session expiry: login wall after Connect invalidates BoardSession + connect_hint
- [x] Live linkedin.com/indeed.com without session → `needs_user` + connect_hint (not silent fail)
- [ ] Production: point extension `API_BASE` / host_permissions at HTTPS deploy (not only localhost)
- [ ] Live LinkedIn Easy Apply smoke with real account (manual; ToS)
