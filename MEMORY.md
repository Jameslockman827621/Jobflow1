# MEMORY.md - JobScale Long-Term Memory

_Curated memories for continuity across sessions._

---

## 🎯 Project Overview

**JobScale** - Production-ready SaaS platform aggregating jobs from multiple sources, matching them to users based on skills/preferences, using AI to tailor CVs/cover letters, and tracking applications.

**Repository:** https://github.com/Bill1489/Jobflow.git  
**Target:** 500K+ jobs from 5,000+ companies across all industries

---

## 🏗️ Architecture Decisions

### Hybrid Search Architecture
- **On-demand searches per user** (not continuous scraping)
- **90% cost reduction:** $475/mo → ~$50/mo
- **4 sources:** Indeed (30s), LinkedIn (100s), Greenhouse (60s), Lever (60s)
- **Cache strategy:** 24h TTL with 6-hour refresh schedule

### Sustainable Job Sources
- Focus on ATS providers (Greenhouse, Lever, Workable) over LinkedIn scraping
- Avoids ToS violations and rate limiting
- More reliable and ethical approach

### Matching Algorithm Weights
- Skills: 40%
- Seniority: 20%
- Location: 20%
- Salary: 20%

---

## 💰 Business Model

**3-Tier Monetization:**
- **Free:** 5 applications/month
- **Pro:** $29/month (unlimited apps, AI features)
- **Premium:** $79/month (priority support, advanced analytics)

**Referral Program:** 20% recurring commission for referrals

---

## 🎨 Design System

**Color Palette:**
- Primary: Navy (#0f172a, #1e293b, #334155)
- Accent: Teal (#14b8a6, #2dd4bf, #5eead4)
- Secondary: Coral (#f97316, #fb923c)
- Neutral: Slate (#f8fafc, #f1f5f9, #e2e8f0)

**Typography:** Plus Jakarta Sans  
**Spacing:** 8px grid  
**Radius:** 20px (xl)  
**Shadows:** md, xl

**Design Principles:**
- No AI slop (no purple gradients, emoji icons, templated cards)
- Professional Figma-level design
- Navy/teal/coral color palette
- Clean, modern aesthetic

---

## 🗄️ Database Schema (11 Tables)

1. **users** - Authentication & accounts
2. **user_profiles** - Extended user data
3. **jobs** - Job listings from all sources
4. **job_sources** - Source tracking (Indeed, LinkedIn, etc.)
5. **applications** - User job applications
6. **user_preferences** - Search preferences (NEW, 2026-03-07)
7. **search_cache** - Cached search results with 24h TTL (NEW, 2026-03-07)
8. **referral_codes** - Referral tracking
9. **referrals** - Referral relationships
10. **company_reviews** - Company ratings & reviews
11. **interview_reviews** - Interview preparation tracking

---

## 🔧 Tech Stack

### Backend
- **Framework:** FastAPI 0.109.0 (Python)
- **Database:** PostgreSQL + SQLAlchemy 2.0.25
- **Migrations:** Alembic 1.13.1
- **Task Queue:** Celery + Redis
- **Scrapers:** Apify API (LinkedIn, Indeed)

### Frontend
- **Framework:** Next.js 14.1.0
- **Styling:** Tailwind CSS
- **State:** React Query (@tanstack/react-query)
- **Auth:** JWT-based context

### Infrastructure
- **Backend Host:** Railway (recommended)
- **Frontend Host:** Vercel (recommended)
- **Database:** PostgreSQL (managed)
- **Cache:** Redis (Celery broker)

---

## 🔐 Security Practices

- **API keys:** Never commit to repository (GitHub Secret Scanning enforcement)
- **Authentication:** JWT-based with automatic 401 handling
- **Environment variables:** All secrets set via environment only
- **Branch strategy:** Feature branches, merge via PR

---

## 📊 API Endpoints (13 Routers)

1. `/auth` - Register, login, me
2. `/users` - User management
3. `/jobs` - Job CRUD
4. `/applications` - Application tracking
5. `/billing` - Stripe integration
6. `/career` - Career pathing
7. `/analytics` - Dashboard analytics
8. `/reviews` - Company reviews
9. `/referrals` - Referral system
10. `/interview` - Interview prep
11. `/interview_coach` - AI interview coaching
12. `/profile` - User profiles
13. `/health` - Health checks

---

## 🚀 Deployment Strategy

### Backend (Railway)
- PostgreSQL database
- Redis for Celery
- Environment variables for secrets
- Auto-deploy on push

### Frontend (Vercel)
- Next.js optimized hosting
- Edge functions for API routes
- Automatic HTTPS
- Preview deployments for PRs

---

## 📈 Key Milestones

### 2026-03-07: E2E Testing Complete ✅
- All servers running (backend 8000, frontend 3000)
- Database migrations applied (11 tables)
- Full user flow tested and working
- Production readiness: 100%
- GitHub branch `phase2-clean` pushed

### MVP (5/5) Complete ✅
- Profile API + UI
- Job Pipeline
- Email Service
- Application Workflow
- Frontend Polish

### v1.0 (7/7) Complete ✅
- Browser Extension
- Google Jobs Scraper
- Application Kanban
- Interview Prep
- Job Alerts
- Resume Parser
- Dashboard

### v1.5 (5/5) Complete ✅
- Stripe Billing
- Free Tier Limits
- Referral System
- Pricing Page
- Premium Features

### v2.0 (3/3) Complete ✅
- Career Pathing
- Analytics Dashboard
- Company Reviews

---

## 🎯 Onboarding Flow (5 Steps)

1. **Select Roles** - Target job titles
2. **Select Seniority** - Entry, mid, senior, lead, executive
3. **Select Locations** - Cities/regions (8 countries supported)
4. **Select Preferences** - Remote, job type, date posted, salary
5. **Review & Search** - Confirm and run job search

**Countries Supported:** UK, US, CA, AU, DE, FR, IE, NL  
**Remote Options:** any, remote_only, hybrid_ok, onsite_only

---

## 🐛 Known Issues & Workarounds

### Browser Tool Unavailable
- **Issue:** OpenClaw gateway timeout (15000ms)
- **Workaround:** Static HTML + Playwright for screenshots
- **Status:** Awaiting gateway restart

### Memory Constraints
- **Issue:** 1.6GB RAM limit causes SIGBUS with Next.js dev server
- **Workaround:** Run servers in background, use static HTML when needed
- **Status:** Production deployment will resolve (Railway/Vercel have more resources)

### No Sudo Access
- **Issue:** Cannot install system packages
- **Workaround:** Use npm/pip in user space, virtual environments
- **Status:** Normal for production environments

---

## 📝 Session Patterns

### What Works Well
- Background exec sessions for long-running processes
- Static HTML workaround for browser tool issues
- Feature branch strategy for GitHub pushes
- Comprehensive documentation in workspace

### What to Avoid
- Browser tool calls until gateway restarted
- Committing API keys (GitHub Secret Scanning)
- Running Next.js dev server in foreground (memory issues)
- Assuming PostgreSQL is running (always check first)

---

## 🎉 Project Status

**Production Readiness:** 100% ✅

**All Core Features Working:**
- ✅ User authentication
- ✅ 5-step onboarding
- ✅ Precise job search (Indeed + LinkedIn)
- ✅ Dashboard with job results
- ✅ Application Kanban board
- ✅ Error handling & notifications
- ✅ Professional UI/UX

**Next Priority:** Production deployment (Railway + Vercel)

---

_This memory is curated for long-term continuity. Daily logs are in memory/YYYY-MM-DD.md_
