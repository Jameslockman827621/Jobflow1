# JobScale - Complete User Flow Walkthrough

**Document Version:** 1.0  
**Last Updated:** March 6, 2026

---

## 🗺️ USER JOURNEY MAP

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        JOBSCALE USER FLOW                                   │
└─────────────────────────────────────────────────────────────────────────────┘

    LANDING PAGE              AUTHENTICATION           ONBOARDING
    ┌──────────┐             ┌──────────┐            ┌──────────┐
    │          │             │          │            │          │
    │  /       │────────────▶│  /login  │───────────▶│  /profile│
    │          │   Click     │          │   Sign up  │          │
    │          │   "Get      │          │   or       │          │
    │          │   Started"  │          │   Login    │          │
    └──────────┘             └──────────┘            └────┬─────┘
                                                          │
                                                          │ Complete
                                                          │ profile
                                                          │
         ┌─────────────────────────────────────────────────┘
         │
         ▼
    ┌──────────────┐         ┌──────────────┐        ┌──────────────┐
    │              │         │              │        │              │
    │  /dashboard  │────────▶│   /kanban    │───────▶│  /pricing    │
    │              │  Apply  │              │ Upgrade│              │
    │  Browse jobs │  jobs   │  Track apps  │ plan   │  Choose tier │
    │              │         │              │        │              │
    └──────┬───────┘         └──────────────┘        └──────┬───────┘
           │                                                │
           │                                                │ Payment
           │                                                │ (Stripe)
           │                                                │
           │         ┌──────────────┐         ┌─────────────┴──────┐
           │         │              │         │                    │
           │         │   /career    │         │   /analytics       │
           │         │              │         │                    │
           └────────▶│  Career      │         │   View stats,      │
                     │  pathing     │         │   funnel, insights │
                     │              │         │                    │
                     └──────────────┘         └────────────────────┘
```

---

## 📍 STEP-BY-STEP FLOW

### **1. LANDING PAGE** (`/`)

**What User Sees:**
- Professional hero section: "Your career, accelerated"
- Value prop: "JobScale finds opportunities that match your skills, tailors your applications with AI"
- Stats bar: 50+ companies, 958 jobs, 77% match accuracy
- 6 feature cards (Smart Matching, AI Applications, Career Pathing, Analytics, Reviews, Interview Coach)
- Dark CTA section: "Ready to accelerate your career?"
- Navigation: Product, Pricing, Company, Sign In, Get Started

**User Actions:**
- Click "Get Started" → Go to `/login` (register mode)
- Click "Sign In" → Go to `/login` (login mode)
- Click "View Demo" → Opens API docs in new tab
- Click feature cards → Scroll to relevant section

**Files:**
- `frontend/src/app/page.tsx`
- `frontend/tailwind.config.ts` (design tokens)

---

### **2. AUTHENTICATION** (`/login`)

**What User Sees:**
- Toggle: "Sign in" vs "Create account"
- Email input
- Password input
- First name, last name (register only)
- Error messages (red banner)
- Loading state on submit

**User Actions:**

#### **Login Flow:**
1. Enter email
2. Enter password
3. Click "Sign In"
4. API call: `POST /api/v1/auth/login`
5. Receive JWT token
6. Token saved to `localStorage`
7. Redirect to `/dashboard`

#### **Register Flow:**
1. Switch to "Create account"
2. Enter first name, last name, email, password
3. Click "Create account"
4. API call: `POST /api/v1/auth/register`
5. Auto-login: `POST /api/v1/auth/login`
6. Token saved to `localStorage`
7. Redirect to `/dashboard`

**Files:**
- `frontend/src/app/login/page.tsx`
- `backend/app/api/auth.py`

**API Endpoints:**
```python
POST /api/v1/auth/register
  Body: { email, password, first_name, last_name }
  Response: { id, email, first_name, last_name }

POST /api/v1/auth/login
  Body: { username (email), password }
  Response: { access_token, token_type }

GET /api/v1/auth/me
  Headers: { Authorization: Bearer <token> }
  Response: { id, email, first_name, last_name, is_premium, subscription_status }
```

---

### **3. PROFILE SETUP** (`/profile`)

**What User Sees:**
- Personal info section (first name, last name, location, timezone)
- Career info (current title, company, years of experience)
- Desired roles (multi-select chips)
- Desired industries (multi-select chips)
- Salary range ($60k - $500k slider)
- Preferences (remote only, relocate, preferred countries)
- Resume text area (paste resume content)
- Skills management (add/remove skills with category, years, proficiency)
- Save button with loading state

**User Actions:**
1. Fill in personal details
2. Add desired roles (e.g., "Software Engineer", "Senior Developer")
3. Add desired industries (e.g., "Technology", "Fintech")
4. Set salary expectations
5. Check preferences (remote only, willing to relocate)
6. Paste resume text (for AI parsing)
7. Add skills:
   - Type skill name (e.g., "Python")
   - Select category (Technical, Soft Skill, Tool, etc.)
   - Set years of experience
   - Set proficiency (Beginner, Intermediate, Advanced, Expert)
   - Click "Add Skill"
8. Click "Save Profile"
9. API call: `PATCH /api/v1/profile/me`
10. Success message
11. Redirect to `/dashboard`

**Files:**
- `frontend/src/app/profile/page.tsx`
- `backend/app/api/profile.py`
- `backend/app/services/resume_parser.py`

**API Endpoints:**
```python
GET /api/v1/profile/me
  Headers: { Authorization: Bearer <token> }
  Response: { profile object with skills array }

PATCH /api/v1/profile/me
  Headers: { Authorization: Bearer <token> }
  Body: { first_name, last_name, location, desired_roles, skills, ... }
  Response: { updated profile object }

POST /api/v1/profile/skills
  Headers: { Authorization: Bearer <token> }
  Body: { name, category, years, proficiency }
  Response: { skill object }
```

**Why This Matters:**
- Profile data powers the matching algorithm
- Skills are compared against job requirements
- Salary/location preferences filter job results
- Resume text is used for AI CV tailoring

---

### **4. DASHBOARD** (`/dashboard`)

**What User Sees:**
- Tab navigation: Jobs | Applications | Profile
- **Jobs Tab:**
  - List of job cards (title, company, location, salary, match score)
  - Filter by remote/hybrid
  - "Apply" button on each card
- **Applications Tab:**
  - List of user's applications
  - Status badges (draft, submitted, interview, offer, rejected)
  - Stage indicators
- **Profile Tab:**
  - Quick profile summary
  - Edit link

**User Actions:**

#### **Browse Jobs:**
1. Click "Jobs" tab
2. See list of matched jobs (sorted by match score)
3. Filter by remote/hybrid
4. Click job card → See details
5. Click "Apply" → Creates application record
6. API call: `POST /api/v1/applications/`
7. Redirect to `/kanban` to track

#### **View Applications:**
1. Click "Applications" tab
2. See all applications with status
3. Click application → See details
4. Update status/stage

**Files:**
- `frontend/src/app/dashboard/page.tsx`
- `frontend/src/components/JobCard.tsx`
- `backend/app/api/jobs.py`
- `backend/app/api/applications.py`
- `backend/app/services/matching.py`

**API Endpoints:**
```python
GET /api/v1/jobs?limit=20&remote=true
  Headers: { Authorization: Bearer <token> }
  Response: [ { id, title, company, location, match_score, ... } ]

POST /api/v1/applications/
  Headers: { Authorization: Bearer <token> }
  Body: { job_id, cover_letter (optional) }
  Response: { application object }

GET /api/v1/applications/
  Headers: { Authorization: Bearer <token> }
  Response: [ { id, job_title, company, status, stage, ... } ]
```

**Matching Algorithm:**
```python
# backend/app/services/matching.py
Score = (
  skills_match * 0.40 +      # 40% - Skills overlap
  seniority_match * 0.20 +   # 20% - Experience level
  location_match * 0.20 +    # 20% - Location preference
  salary_match * 0.20        # 20% - Salary range
)
```

---

### **5. KANBAN BOARD** (`/kanban`)

**What User Sees:**
- 7 columns: Wishlist | Applied | Phone Screen | Technical | Onsite | Offer | Rejected
- Application cards in each column
- Drag-and-drop functionality
- Match score badge on each card
- Application count at top

**User Actions:**
1. See all applications organized by stage
2. Drag card from "Applied" to "Phone Screen"
3. Drop → API call updates stage
4. Card moves to new column
5. Color-coded by stage (blue, yellow, orange, purple, green, red)

**Files:**
- `frontend/src/app/kanban/page.tsx`
- `backend/app/api/applications.py`

**API Endpoints:**
```python
PATCH /api/v1/applications/{id}
  Headers: { Authorization: Bearer <token> }
  Body: { stage: "phone_screen", status: "interview" }
  Response: { updated application object }
```

**Stage Mapping:**
| Stage | Status | Color |
|-------|--------|-------|
| Wishlist | draft | Gray |
| Applied | submitted | Blue |
| Phone Screen | interview | Yellow |
| Technical | interview | Orange |
| Onsite | interview | Purple |
| Offer | offer | Green |
| Rejected | rejected | Red |

---

### **6. PRICING & UPGRADE** (`/pricing`)

**What User Sees:**
- Toggle: Monthly | Yearly (Save 20%)
- 3 pricing cards:
  - **Free:** $0 - 5 apps/month, basic AI
  - **Pro:** $29/mo - Unlimited apps, priority AI, analytics
  - **Premium:** $79/mo - Everything + interview coach, career coaching
- Feature comparison lists
- FAQ accordion (6 questions)
- Referral program section

**User Actions:**
1. Review plans
2. Toggle monthly/yearly pricing
3. Click "Start Free Trial" on Pro plan
4. API call: `POST /api/v1/billing/checkout`
5. Receive Stripe checkout URL
6. Redirect to Stripe Checkout
7. User enters payment info
8. Stripe redirects back to `/billing/success`
9. Webhook updates user's subscription status

**Files:**
- `frontend/src/app/pricing/page.tsx`
- `backend/app/api/billing.py`

**API Endpoints:**
```python
POST /api/v1/billing/checkout
  Headers: { Authorization: Bearer <token> }
  Body: { plan: "pro_monthly", success_url, cancel_url }
  Response: { checkout_url, session_id }

GET /api/v1/billing/subscription
  Headers: { Authorization: Bearer <token> }
  Response: { status, plan, current_period_end, applications_used, applications_limit }
```

**Plans:**
| Feature | Free | Pro | Premium |
|---------|------|-----|---------|
| Applications/month | 5 | Unlimited | Unlimited |
| AI CV tailoring | Basic | Priority | Priority |
| Match score filter | Any | 80%+ | 90%+ |
| Interview prep | ❌ | ✅ | ✅ |
| Cover letters | ❌ | ✅ | ✅ |
| Job alerts | ❌ | Daily | Real-time |
| Analytics | ❌ | ✅ | ✅ |
| Interview coach | ❌ | ❌ | ✅ |
| Career coaching | ❌ | ❌ | Monthly 1-on-1 |

---

### **7. CAREER PATHING** (`/career`)

**What User Sees:**
- Tabs: Analysis | Goals | Recommendations
- Current level card (e.g., "Mid-Level Engineer")
- Progress bar to next level
- Career ladder (5 levels with salary ranges)
- Skill gaps section (Leadership, System Design, Mentoring)
- Sidebar: Next milestone card, recommended courses

**User Actions:**
1. View current level and progress
2. See skill gaps with priority badges
3. View career ladder progression
4. Click "Create Action Plan" → Generates milestones
5. View recommended learning courses

**Files:**
- `frontend/src/app/career/page.tsx`
- `backend/app/api/career.py`
- `backend/app/services/career_pathing.py`

**API Endpoints:**
```python
GET /api/v1/career/analysis
  Headers: { Authorization: Bearer <token> }
  Response: { current_level, progress, skill_gaps, recommendations }

GET /api/v1/career/paths
  Headers: { Authorization: Bearer <token> }
  Response: [ { level, title, years, salary_min, salary_max } ]

GET /api/v1/career/salary?role=software_engineer
  Headers: { Authorization: Bearer <token> }
  Response: { role, min, max, median, percentiles }
```

---

### **8. ANALYTICS DASHBOARD** (`/analytics`)

**What User Sees:**
- Profile completeness bar (80%)
- 4 metric cards:
  - Total Applications (15)
  - Interview Rate (20%)
  - Offer Rate (6.7%)
  - Response Rate (73%)
- Application funnel visualization
- Top hiring companies list
- Trending skills badges
- Remote opportunities chart (35%)

**User Actions:**
1. View application metrics
2. See funnel drop-off points
3. Browse top companies hiring
4. View trending skills in market
5. Export report (PDF/CSV)

**Files:**
- `frontend/src/app/analytics/page.tsx`
- `backend/app/api/analytics.py`

**API Endpoints:**
```python
GET /api/v1/analytics/overview
  Headers: { Authorization: Bearer <token> }
  Response: { profile_completeness, applications_total, interview_rate, offer_rate, response_rate }

GET /api/v1/analytics/market-insights
  Headers: { Authorization: Bearer <token> }
  Response: { top_companies, trending_skills, remote_percentage }
```

---

### **9. COMPANY REVIEWS** (`/reviews`)

**What User Sees:**
- Left sidebar: Company list with ratings
- Main area: Selected company details
  - Company header (logo, name, overall rating)
  - Rating breakdown (Work-Life, Culture, Compensation, Opportunities)
  - "Recommend to Friend" circular chart
  - Recent reviews list
- "Write a Review" button → Modal form

**User Actions:**
1. Click company in sidebar
2. Read reviews and ratings
3. Click "Write a Review"
4. Fill form (company, rating, title, pros, cons)
5. Submit → API saves review
6. Review appears in list

**Files:**
- `frontend/src/app/reviews/page.tsx`
- `backend/app/api/reviews.py`
- `backend/app/models/review.py`

**API Endpoints:**
```python
GET /api/v1/reviews/companies
  Headers: { Authorization: Bearer <token> }
  Response: { companies: [ { name, rating, review_count } ] }

GET /api/v1/reviews/company/{name}
  Headers: { Authorization: Bearer <token> }
  Response: { company, rating, reviews: [ ... ] }

POST /api/v1/reviews/company
  Headers: { Authorization: Bearer <token> }
  Body: { company_name, overall_rating, title, pros, cons }
  Response: { review object }
```

---

### **10. INTERVIEW COACH** (`/interview-coach`)

**What User Sees:**
- Role selector dropdown
- "Start Mock Interview" button
- Chat interface with AI
- Real-time feedback scores (Clarity, Technical, Structure)
- Question history

**User Actions:**
1. Select target role (Software Engineer, PM, etc.)
2. Click "Start Mock Interview"
3. AI asks first question
4. User types/speaks answer
5. AI provides feedback
6. Continue to next question
7. View final score and recommendations

**Files:**
- `frontend/src/app/interview-coach/page.tsx`
- `backend/app/api/interview_coach.py`
- `backend/app/services/interview_prep.py`

**API Endpoints:**
```python
POST /api/v1/interview/sessions
  Headers: { Authorization: Bearer <token> }
  Body: { role, seniority }
  Response: { session_id, first_question }

POST /api/v1/interview/sessions/{id}/response
  Headers: { Authorization: Bearer <token> }
  Body: { answer }
  Response: { feedback, next_question, scores }
```

---

## 🔄 COMPLETE USER JOURNEY EXAMPLE

### **Sarah's Story: From Sign-Up to Job Offer**

**Day 1: Discovery & Sign-Up**
1. Lands on `/` from Google search
2. Reads value prop: "AI-powered career acceleration"
3. Clicks "Get Started"
4. Registers: sarah@dev.com, password
5. Auto-login, redirected to `/dashboard`
6. Prompted to complete profile

**Day 1: Profile Setup**
1. Goes to `/profile`
2. Fills in:
   - Name: Sarah Chen
   - Location: London, UK
   - Current title: Software Engineer
   - Years of experience: 4
   - Desired roles: Senior Software Engineer
   - Desired industries: Technology, Fintech
   - Salary: £90k-£140k
   - Remote only: No
   - Skills: Python (5 yrs, Expert), React (3 yrs, Advanced), AWS (2 yrs, Intermediate)
   - Resume: Pastes full CV text
3. Saves profile

**Day 1: Job Search**
1. Goes to `/dashboard` → Jobs tab
2. Sees 47 matched jobs (sorted by match score)
3. Filters: Remote = True
4. Sees 23 remote jobs
5. Applies to 5 jobs:
   - Stripe (Senior Engineer, 92% match)
   - Airbnb (Senior Engineer, 88% match)
   - GitLab (Senior Engineer, 85% match)
   - Figma (Senior Engineer, 83% match)
   - Monzo (Senior Engineer, 81% match)
6. Each application creates record in `/kanban`

**Day 2: Upgrade to Pro**
1. Tries to apply to 6th job
2. Sees modal: "Free tier limit reached (5/5 applications)"
3. Clicks "Upgrade to Pro"
4. Goes to `/pricing`
5. Selects Pro plan ($29/mo)
6. Clicks "Start Free Trial"
7. Redirected to Stripe Checkout
8. Enters card details
9. Redirected back to `/billing/success`
10. Subscription status: "active"
11. Application limit: unlimited

**Day 3: Interview Prep**
1. Gets email: "Stripe viewed your application"
2. Moves Stripe card to "Phone Screen" in `/kanban`
3. Goes to `/interview-coach`
4. Selects role: "Senior Software Engineer"
5. Starts mock interview
6. Practices 5 questions with AI feedback
7. Scores: Clarity 8/10, Technical 7/10, Structure 9/10

**Day 7: Career Pathing**
1. Goes to `/career`
2. Sees current level: "Mid-Level Engineer (50% to Senior)"
3. Skill gaps identified:
   - Leadership (40% - High Priority)
   - System Design (60% - Medium Priority)
   - Mentoring (80% - On Track)
4. Clicks "Create Action Plan"
5. Gets 6-month roadmap to Senior level

**Day 14: Analytics Review**
1. Goes to `/analytics`
2. Sees metrics:
   - Applications: 23
   - Interview Rate: 26% (6 interviews)
   - Offer Rate: 8.7% (2 offers)
   - Response Rate: 78%
3. Funnel shows drop-off at Technical Interview stage
4. Decides to practice more system design

**Day 21: Company Research**
1. Has onsite at Figma
2. Goes to `/reviews`
3. Clicks "Figma"
4. Reads 42 reviews
5. Sees ratings:
   - Work-Life: 4.1/5
   - Culture: 4.5/5
   - Compensation: 4.3/5
6. 82% would recommend to friend
7. Feels confident about offer

**Day 30: Offer Decision**
1. Has 2 offers: Stripe (£120k), Figma (£115k)
2. Moves both to "Offer" column in `/kanban`
3. Uses salary negotiation script from Premium features
4. Accepts Stripe offer
5. Marks other applications as "withdrawn"

**Day 31: Referral**
1. Goes to `/profile` → Referrals tab
2. Gets unique referral link
3. Shares link with 3 friends on LinkedIn
4. 2 friends sign up → Sarah gets £20 credit
5. 1 friend upgrades to Pro → Sarah gets £50 credit
6. Total earned: £70

---

## 📊 CONVERSION FUNNEL

```
Landing Page Visitors (100%)
    │
    ├─▶ Click "Get Started" (40%)
    │       │
    │       ├─▶ Complete Registration (80% of clickers = 32%)
    │       │       │
    │       │       ├─▶ Complete Profile (60% = 19%)
    │       │       │       │
    │       │       │       ├─▶ Apply to First Job (70% = 13%)
    │       │       │       │       │
    │       │       │       │       ├─▶ Hit Free Tier Limit (90% = 12%)
    │       │       │       │       │       │
    │       │       │       │       │       ├─▶ Upgrade to Pro (15% = 1.8%)
    │       │       │       │       │       │       │
    │       │       │       │       │       │       ├─▶ Active After 30 Days (70% = 1.26%)
    │       │       │       │       │       │               │
    │       │       │       │       │       │               └─▶ Refer Friend (20% = 0.25%)
```

**Key Metrics:**
- **Visitor → Registered:** 32%
- **Registered → Active:** 19%
- **Active → Paying:** 1.8%
- **Paying → Retained (30d):** 1.26%
- **Retained → Referrer:** 0.25%

---

## 🔐 AUTHENTICATION FLOW

```
┌─────────────────────────────────────────────────────────────┐
│                    JWT Authentication Flow                  │
└─────────────────────────────────────────────────────────────┘

Frontend                          Backend                    Database
   │                                │                           │
   │  POST /auth/register           │                           │
   ├───────────────────────────────▶│                           │
   │  { email, password, ... }      │                           │
   │                                │  Hash password            │
   │                                ├──────────────────────────▶│
   │                                │  Create user              │
   │                                │◀──────────────────────────┤
   │                                │  Return user object       │
   │◀───────────────────────────────┤                           │
   │                                │                           │
   │  POST /auth/login              │                           │
   ├───────────────────────────────▶│                           │
   │  { username, password }        │  Find user                │
   │                                ├──────────────────────────▶│
   │                                │  Verify password          │
   │                                │◀──────────────────────────┤
   │                                │  Create JWT               │
   │  { access_token }              │                           │
   │◀───────────────────────────────┤                           │
   │                                │                           │
   │  Store token in localStorage   │                           │
   │                                │                           │
   │  GET /api/v1/jobs              │                           │
   ├───────────────────────────────▶│                           │
   │  Authorization: Bearer <token> │  Decode JWT               │
   │                                │  Extract user_id          │
   │                                │  Query jobs for user      │
   │                                ├──────────────────────────▶│
   │                                │◀──────────────────────────┤
   │  [jobs array]                  │                           │
   │◀───────────────────────────────┤                           │
   │                                │                           │
```

---

## 💳 PAYMENT FLOW

```
┌─────────────────────────────────────────────────────────────┐
│                    Stripe Payment Flow                      │
└─────────────────────────────────────────────────────────────┘

User          Frontend         Backend         Stripe         Database
  │               │               │               │               │
  │  Click "Pro"  │               │               │               │
  ├──────────────▶│               │               │               │
  │               │               │               │               │
  │               │ POST /checkout│               │               │
  │               ├──────────────▶│               │               │
  │               │ { plan: "pro" }               │               │
  │               │               │               │               │
  │               │               │ Create Session│               │
  │               │               ├──────────────▶│               │
  │               │               │               │               │
  │               │               │◀──────────────┤               │
  │               │               │ { session_id, │               │
  │               │               │   checkout_url}               │
  │               │               │               │               │
  │               │ { checkout_url }              │               │
  │               │◀──────────────┤               │               │
  │               │               │               │               │
  │  Redirect to Stripe Checkout  │               │               │
  ├──────────────────────────────▶│               │               │
  │               │               │               │               │
  │  Enter card details           │               │               │
  ├──────────────────────────────────────────────▶│               │
  │               │               │               │               │
  │               │               │               │ Process payment
  │               │               │               │               │
  │  Redirect to success URL      │               │               │
  ├──────────────▶│               │               │               │
  │               │               │               │               │
  │               │               │ Webhook event │               │
  │               │               │◀──────────────┤               │
  │               │               │ checkout.session.completed    │
  │               │               │               │               │
  │               │               │ Update user subscription      │
  │               │               ├──────────────────────────────▶│
  │               │               │               │               │
  │               │               │               │  User is now Pro
  │               │               │               │◀──────────────┤
  │               │               │               │               │
  │  See "Upgrade Complete!"      │               │               │
  │◀──────────────┤               │               │               │
  │               │               │               │               │
```

---

## 🎯 KEY USER ACTIONS & API CALLS

| User Action | Frontend Route | API Endpoint | Method |
|-------------|---------------|--------------|--------|
| Register | `/login` | `/api/v1/auth/register` | POST |
| Login | `/login` | `/api/v1/auth/login` | POST |
| View profile | `/profile` | `/api/v1/profile/me` | GET |
| Update profile | `/profile` | `/api/v1/profile/me` | PATCH |
| Add skill | `/profile` | `/api/v1/profile/skills` | POST |
| Browse jobs | `/dashboard` | `/api/v1/jobs` | GET |
| Apply to job | `/dashboard` | `/api/v1/applications/` | POST |
| View applications | `/kanban` | `/api/v1/applications/` | GET |
| Update application stage | `/kanban` | `/api/v1/applications/{id}` | PATCH |
| View career path | `/career` | `/api/v1/career/analysis` | GET |
| View analytics | `/analytics` | `/api/v1/analytics/overview` | GET |
| View company reviews | `/reviews` | `/api/v1/reviews/companies` | GET |
| Write review | `/reviews` | `/api/v1/reviews/company` | POST |
| Start interview practice | `/interview-coach` | `/api/v1/interview/sessions` | POST |
| Upgrade to Pro | `/pricing` | `/api/v1/billing/checkout` | POST |
| View subscription | `/pricing` | `/api/v1/billing/subscription` | GET |

---

## 📱 MOBILE RESPONSIVENESS

All pages are responsive with breakpoints:

| Screen Size | Breakpoint | Layout Changes |
|-------------|------------|----------------|
| Mobile | < 640px | Single column, stacked cards, hamburger menu |
| Tablet | 640px - 1024px | 2-column grid, condensed navigation |
| Desktop | > 1024px | Full layout, sidebars visible |

**Mobile-Specific Optimizations:**
- Touch-friendly buttons (min 44px height)
- Swipeable job cards
- Collapsible filters
- Bottom navigation bar (optional enhancement)

---

## 🔔 NOTIFICATIONS (Future Enhancement)

Currently not implemented, planned:

| Trigger | Channel | Template |
|---------|---------|----------|
| New job match | Email | "5 new jobs match your profile" |
| Application viewed | Email | "Stripe viewed your application" |
| Interview request | Email + Push | "Interview invitation from Airbnb" |
| Payment success | Email | "Welcome to JobScale Pro!" |
| Payment failed | Email | "Action required: Update payment method" |
| Referral signup | Email | "You earned $10 from [Friend's name]" |

---

## 📈 ANALYTICS EVENTS (Future Enhancement)

Tracked events for product analytics:

```javascript
// Example: PostHog/Mixpanel events
analytics.track('user_registered', { email, source })
analytics.track('profile_completed', { completeness_score })
analytics.track('job_applied', { job_id, company, match_score })
analytics.track('application_stage_changed', { from, to })
analytics.track('upgrade_started', { plan })
analytics.track('payment_completed', { plan, amount })
analytics.track('interview_practice_started', { role })
analytics.track('review_written', { company, rating })
```

---

## ✅ COMPLETENESS CHECK

| Flow | Status | Notes |
|------|--------|-------|
| Registration | ✅ Complete | JWT auth working |
| Login | ✅ Complete | Token stored in localStorage |
| Profile setup | ✅ Complete | All fields implemented |
| Job browsing | ✅ Complete | Matching algorithm working |
| Application submission | ✅ Complete | Creates DB record |
| Kanban tracking | ✅ Complete | Drag-drop working |
| Pricing display | ✅ Complete | 3 tiers with features |
| Stripe checkout | ⚠️ Code complete, needs API keys |
| Career pathing | ✅ Complete | Analysis + visualization |
| Analytics | ✅ Complete | Metrics + funnel |
| Company reviews | ✅ Complete | CRUD operations |
| Interview coach | ✅ Complete | AI-powered Q&A |
| Email notifications | ⚠️ Code complete, needs SendGrid key |
| Referral program | ⚠️ Code complete, needs testing |

---

**This document represents the complete user flow as of March 6, 2026.**
