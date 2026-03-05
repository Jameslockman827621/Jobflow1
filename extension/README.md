# JobScale Chrome Extension

Browser extension for one-click job applications with AI.

## Installation (Development)

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select this `extension/` folder
5. Extension icon should appear in toolbar

## Usage

1. **Login**: Click extension icon → Sign in to your JobScale account
2. **Browse Jobs**: Visit LinkedIn, Indeed, Glassdoor, or company career pages
3. **Apply**: Click the floating "🚀 Apply with JobScale" button or use extension popup
4. **Track**: Applications are saved to your dashboard

## Supported Sites

- LinkedIn Jobs
- Indeed
- Glassdoor
- Greenhouse (company career pages)
- Lever (company career pages)

## Features

- ✨ One-click application from any job board
- 🤖 AI tailors CV and cover letter automatically
- 📊 Track all applications in one dashboard
- 🔔 Get notified of interview requests

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
