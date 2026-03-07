# 🚀 JobScale Production TODO List

**Created:** 2026-03-07  
**Priority:** Critical gaps first, then enhancements

---

## 🔴 CRITICAL (BLOCKING) - Must Fix Before Testing

### 1. Fix Frontend → Backend API Integration
- [ ] Add API proxy rewrites in `next.config.js`
- [ ] Configure backend URL for development
- [ ] Configure backend URL for production
- [ ] Test API calls from frontend

**Files to modify:**
- `frontend/next.config.js`

**Expected:** Frontend can call `/api/v1/*` and it proxies to backend

---

### 2. Create Authentication Hook/Context
- [ ] Create `src/lib/auth.ts` with useAuth hook
- [ ] Implement JWT token storage (localStorage)
- [ ] Add login/logout functions
- [ ] Add token refresh logic
- [ ] Add protected route handling
- [ ] Test auth flow end-to-end

**Files to create:**
- `frontend/src/lib/auth.tsx` (React Context)
- `frontend/src/hooks/useAuth.ts`

**Expected:** `useAuth()` hook works in all components

---

### 3. Create Database Migrations
- [ ] Initialize Alembic (if not done)
- [ ] Generate migration for UserPreferences model
- [ ] Generate migration for SearchCache model
- [ ] Run migrations
- [ ] Verify tables created

**Commands:**
```bash
cd backend
source venv/bin/activate
alembic revision --autogenerate -m "Add preferences and search_cache tables"
alembic upgrade head
```

**Expected:** Database has all 12 tables

---

### 4. Update Environment Variables
- [ ] Generate secure SECRET_KEY
- [ ] Set DEBUG=false for production
- [ ] Add production DATABASE_URL
- [ ] Add OPENAI_API_KEY
- [ ] Add STRIPE keys
- [ ] Add SENDGRID API key
- [ ] Document all required env vars

**Files to modify:**
- `backend/.env`
- `backend/.env.example`
- `frontend/.env.local`
- `frontend/.env.example`

**Expected:** Production-ready environment configuration

---

## 🟡 HIGH PRIORITY - Must Fix Before Production

### 5. Create Missing Frontend Pages
- [ ] Create `/dashboard` page (main user dashboard)
- [ ] Create `/kanban` page (application tracking)
- [ ] Complete `/pricing` page
- [ ] Add navigation between pages
- [ ] Add protected routes (redirect if not logged in)

**Files to create:**
- `frontend/src/app/dashboard/page.tsx`
- `frontend/src/app/kanban/page.tsx`
- `frontend/src/app/pricing/page.tsx`

**Expected:** All main pages exist and are accessible

---

### 6. Add Input Validation
- [ ] Add required field validation (onboarding)
- [ ] Add email format validation (login/register)
- [ ] Add salary range validation
- [ ] Add country/location validation
- [ ] Add real-time validation feedback
- [ ] Add form submission blocking until valid

**Files to modify:**
- `frontend/src/app/onboarding/page.tsx`
- `frontend/src/app/login/page.tsx`
- `frontend/src/app/register/page.tsx`

**Expected:** Invalid forms can't be submitted

---

### 7. Add Error Handling
- [ ] Add retry logic for API calls
- [ ] Add timeout handling
- [ ] Add specific error messages
- [ ] Add network error handling
- [ ] Add token expiration handling
- [ ] Add 429 rate limit handling

**Files to modify:**
- `frontend/src/lib/api.ts` (create if needed)
- `frontend/src/app/onboarding/page.tsx`
- All API-calling components

**Expected:** Graceful error handling throughout

---

### 8. Add Loading States
- [ ] Add loading spinner for onboarding search
- [ ] Add loading states for all API calls
- [ ] Add skeleton loaders for content
- [ ] Add button loading states
- [ ] Add page transition loading

**Files to modify:**
- All pages with API calls

**Expected:** No UI freezes during loading

---

### 9. Fix Backend Import Dependencies
- [ ] Document venv activation requirement
- [ ] Add startup script
- [ ] Add Docker development setup
- [ ] Add requirements.txt verification

**Files to create:**
- `backend/start.sh`
- `DOCKER-DEV.md`

**Expected:** Clear instructions for running backend

---

### 10. Configure Production Celery
- [ ] Update Celery broker URL for production
- [ ] Add Redis cloud configuration
- [ ] Add worker scaling configuration
- [ ] Add Celery monitoring (Flower)
- [ ] Test background jobs

**Files to modify:**
- `backend/app/tasks/__init__.py`
- `backend/.env`

**Expected:** Celery works in production

---

## 🟢 MEDIUM PRIORITY - Should Have

### 11. Add API Utility Layer
- [ ] Create centralized API client
- [ ] Add request/response interceptors
- [ ] Add automatic token refresh
- [ ] Add error normalization
- [ ] Add request cancellation

**Files to create:**
- `frontend/src/lib/api.ts`

---

### 12. Add Form Components
- [ ] Create reusable Input component
- [ ] Create reusable Select component
- [ ] Create reusable Checkbox component
- [ ] Create reusable Button component
- [ ] Add validation props

**Files to create:**
- `frontend/src/components/ui/Input.tsx`
- `frontend/src/components/ui/Select.tsx`
- `frontend/src/components/ui/Checkbox.tsx`
- `frontend/src/components/ui/Button.tsx`

---

### 13. Add Toast Notifications
- [ ] Install react-hot-toast or similar
- [ ] Create toast utility
- [ ] Add success toasts
- [ ] Add error toasts
- [ ] Add loading toasts

**Files to create:**
- `frontend/src/components/ui/Toast.tsx`
- `frontend/src/lib/toast.ts`

---

### 14. Add Responsive Design
- [ ] Test all pages on mobile
- [ ] Fix mobile layout issues
- [ ] Add mobile navigation
- [ ] Test on tablet
- [ ] Add responsive breakpoints

---

### 15. Add SEO & Metadata
- [ ] Add page titles
- [ ] Add meta descriptions
- [ ] Add Open Graph tags
- [ ] Add favicon
- [ ] Add sitemap.xml

---

## 🔵 LOW PRIORITY - Nice to Have

### 16. Add Unit Tests
- [ ] Backend API tests
- [ ] Scraper tests
- [ ] Frontend component tests
- [ ] Integration tests

---

### 17. Add Monitoring
- [ ] Add Sentry for error tracking
- [ ] Add performance monitoring
- [ ] Add uptime monitoring
- [ ] Add logging configuration

---

### 18. Add Rate Limiting
- [ ] Add SlowAPI to backend
- [ ] Configure rate limits per endpoint
- [ ] Add rate limit headers
- [ ] Add rate limit error responses

---

### 19. Add API Documentation
- [ ] Customize Swagger UI
- [ ] Add endpoint descriptions
- [ ] Add request/response examples
- [ ] Add authentication docs

---

### 20. Add Analytics
- [ ] Add Google Analytics
- [ ] Add conversion tracking
- [ ] Add user behavior tracking
- [ ] Add error tracking

---

## 📊 PROGRESS TRACKING

### Critical (4 items)
- [ ] 1. API Integration
- [ ] 2. Auth Hook
- [ ] 3. Migrations
- [ ] 4. Environment

### High (6 items)
- [ ] 5. Missing Pages
- [ ] 6. Validation
- [ ] 7. Error Handling
- [ ] 8. Loading States
- [ ] 9. Dependencies
- [ ] 10. Celery

### Medium (5 items)
- [ ] 11. API Utility
- [ ] 12. Form Components
- [ ] 13. Toasts
- [ ] 14. Responsive
- [ ] 15. SEO

### Low (5 items)
- [ ] 16. Tests
- [ ] 17. Monitoring
- [ ] 18. Rate Limiting
- [ ] 19. Documentation
- [ ] 20. Analytics

---

## 🎯 CURRENT SPRINT

**Focus:** Critical items (1-4)

**Goal:** Make app functional for end-to-end testing

**Estimated time:** 2-3 hours

---

## 📝 COMPLETION CRITERIA

### Phase 1 (Critical - Done When):
- ✅ User can register/login
- ✅ User can complete onboarding
- ✅ Job search returns results
- ✅ Results display correctly
- ✅ Data persists in database

### Phase 2 (High - Done When):
- ✅ All pages exist and work
- ✅ Forms validated
- ✅ Errors handled gracefully
- ✅ Loading states everywhere
- ✅ Production environment ready

### Phase 3 (Medium - Done When):
- ✅ Code is DRY and maintainable
- ✅ Good UX throughout
- ✅ Mobile-friendly
- ✅ SEO optimized

### Phase 4 (Low - Done When):
- ✅ Tests cover critical paths
- ✅ Monitoring in place
- ✅ Rate limiting configured
- ✅ Documentation complete

---

## 🚀 START COMMAND

```bash
cd /home/admin/.openclaw/workspace

# Begin with critical items
# Start with Item 1: API Integration
```

---

**Status:** Ready to start development  
**Next:** Item 1 - Fix Frontend API Integration
