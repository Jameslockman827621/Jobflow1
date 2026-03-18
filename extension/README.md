# JobScale Chrome Extension

Browser extension for auto-applying to jobs you've selected in your dashboard.

## How It Works

1. **Select jobs in dashboard**: On your JobScale dashboard, check "Auto-apply" on jobs you want to apply to
2. **Visit job pages**: Browse LinkedIn, Indeed, Glassdoor, or company career pages
3. **Auto-apply**: When you visit a job page that matches a selected job, the extension automatically starts the application (opens the job URL, creates application record)
4. **Manual apply**: The "🚀 Apply with JobScale" button opens your dashboard for jobs not in your auto-apply list

## Installation (Development)

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select this `extension/` folder
5. Extension icon should appear in toolbar

## Setup

1. **Login**: Sign in at http://localhost:3000/login (or your JobScale URL)
2. **Sync token**: Visit your dashboard at http://localhost:3000/dashboard - the extension syncs your auth token automatically
3. **Select jobs**: Check "Auto-apply" on jobs you want the extension to apply to when you visit them

## Supported Sites

- LinkedIn Jobs
- Indeed
- Glassdoor
- Greenhouse (company career pages)
- Lever (company career pages)

## Features

- ✨ Auto-apply when you visit job pages matching your dashboard selections
- 📋 Select which jobs to auto-apply in the dashboard
- 🤖 AI tailors CV and cover letter
- 📊 Track all applications in one dashboard

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
