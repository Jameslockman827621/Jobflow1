# JobScale Chrome Extension

Select jobs in the extension → Click Apply → Extension opens all job URLs and starts applications for you.

## How It Works

1. **Open extension** – Click the JobScale icon in your toolbar
2. **Select jobs** – Check the boxes next to jobs you want to apply to (from your dashboard search)
3. **Click Apply** – Extension opens each job URL in a new tab and starts the application. No need to visit each page manually.

## Installation (Development)

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select this `extension/` folder
5. Extension icon should appear in toolbar

## Setup

1. **Login** – Sign in at http://localhost:3000/login
2. **Sync token** – Visit your dashboard at http://localhost:3000/dashboard (extension syncs your auth token)
3. **Run a search** – On the dashboard, run a job search so jobs appear
4. **Select & Apply** – In the extension popup, check jobs and click "Apply to Selected Jobs"

## Features

- ✨ Select jobs in extension, click Apply → opens all URLs automatically
- 📋 No need to visit each job page – extension does it for you
- 🤖 AI tailors CV and cover letter
- 📊 Track all applications in dashboard

## Building for Production

```bash
# Install dependencies (if any)
npm install

# Build (if using TypeScript/React)
npm run build

# Load packed extension or publish to Chrome Web Store
```

## Permissions

- `activeTab` - Detect job postings on current page
- `storage` - Save login token and preferences
- `tabs` - Open dashboard
- `contextMenus` - Right-click "Apply with JobScale" option

## Icons

Replace placeholder icons in `icons/` folder with actual JobScale branding.
