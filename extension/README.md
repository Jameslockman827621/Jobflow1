# JobScale Chrome Extension

Select jobs in the extension → Apply → opens job URLs and auto-fills applications using your JobScale profile.

## Installation (Development)

1. Open Chrome → `chrome://extensions/`
2. Enable **Developer mode**
3. **Load unpacked** → select this `extension/` folder

## Setup (local or production)

1. Open the extension **Options** page (right-click icon → Options).
2. Set:
   - **API base** — e.g. `http://localhost:8000/api/v1` or `https://api.yourdomain.com/api/v1`
   - **Dashboard URL** — e.g. `http://localhost:3000` or `https://app.yourdomain.com`
3. Sign in on the dashboard. Visiting the dashboard syncs your auth token into the extension (or use **Get extension token** from the app if offered).
4. Run a job search on the dashboard so jobs appear in the popup.
5. **Connect boards** (LinkedIn / Indeed) from the dashboard when using Easy Apply — the extension syncs session cookies via `board-sessions/.../from-cookies`.

Popup, background, content script, and form-filler all read `api_base` / `dashboard_url` from `chrome.storage` (defaults are localhost for local dev only).

## Features

- Select jobs → Apply opens each URL and starts fill/submit flows
- Form filler for Greenhouse / Lever / Ashby / Workday / LinkedIn / Indeed patterns
- Connect LinkedIn & Indeed for headless Easy Apply sessions
- Long-lived extension JWT (`POST /auth/extension-token`) for background sync
- Icons: real 16 / 48 / 128 PNGs under `icons/`

## Permissions

- `storage` — token, API/dashboard bases, pending application id
- `tabs` / `cookies` — Connect boards + open dashboard
- `host_permissions` — localhost (dev) plus production HTTPS app/API hosts in `manifest.json`
- `contextMenus` — Connect LinkedIn / Indeed shortcuts

## Production notes

- Configure Options **before** expecting Connect or autofill to hit your API.
- Pack/publish this folder as-is (Manifest V3; no separate `npm run build` step for this tree).
- See `CONNECT-BOARDS-E2E.md` in the repo root for the Connect → Easy Apply path.
