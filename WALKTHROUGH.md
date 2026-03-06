# JobScale - Product Walkthrough

A complete tour of the SaaS platform.

---

## 🏠 Landing Page (`/`)

**What users see:**
- Hero section: "Invest in Your Career"
- Value proposition: AI-powered job search
- Feature highlights (Smart Matching, AI Applications, Career Growth)
- MVP Status indicator
- CTA: "Get Started" → `/login`

---

## 🔐 Authentication (`/login`)

**Features:**
- Toggle between Sign In / Register
- Email + password authentication
- JWT token storage
- Auto-redirect to dashboard after login

**User flow:**
1. Enter email/password
2. Click "Sign In" or "Create Account"
3. Token saved to localStorage
4. Redirected to `/dashboard`

---

## 📊 Dashboard (`/dashboard`)

**Tabs:**

### Jobs Tab
- List of available jobs from scrapers
- Each job shows:
  - Title, company, location
  - Salary range (if available)
  - Remote/Hybrid badges
  - Match score percentage (color-coded)
  - "View Job" → external URL
  - "Apply Now" → creates application

### Applications Tab
- List of user's applications
- Status badges: draft, submitted, interviewing, offered, rejected
- Stage indicators: not_started, applied, phone_screen, technical, onsite
- Match score for each application
- Created date

### Profile Tab (placeholder)
- Links to full profile page

---

## 👤 Profile Management (`/profile`)

**Sections:**

### Personal Information
- First/Last name
- Location (e.g., "London, UK")
- Years of experience
- Current title
- Current company

### Job Preferences
- Min/Max salary
- Remote only checkbox
- Willing to relocate checkbox
- Preferred countries (comma-separated)

### Skills
- Add skills with Enter key
- Visual skill tags with remove (×) button
- Each skill has: name, category, years, proficiency

### Actions
- "Save Profile" button
- Resume upload (parses PDF and auto-fills)

---

## 📋 Application Kanban (`/kanban`)

**7 Columns (drag-drop):**
1. **Wishlist** - Jobs saved for later
2. **Applied** - Applications submitted
3. **Phone Screen** - First interview stage
4. **Technical** - Technical interview
5. **Onsite** - Final round
6. **Offer** - Received offer
7. **Rejected** - Not selected

**Features:**
- Drag applications between columns
- Auto-updates status based on stage
- Shows match score on each card
- Application count per column
- Top stats: total applications, offers

---

## 💰 Pricing Page (`/pricing`)

**3 Plans:**

### Free ($0)
- 5 applications/month
- Basic AI CV tailoring
- Job matching
- Application tracking

### Pro ($29/mo) - Highlighted
- Unlimited applications
- Priority AI processing
- Advanced matching (80%+)
- Interview prep questions
- Cover letter generation
- Daily job alerts
- Application analytics

### Premium ($79/mo)
- Everything in Pro
- AI Interview Coach
- Resume review by experts
- Salary negotiation scripts
- Career pathing
- Recruiter network access
- 1-on-1 career coaching (monthly)

**Features:**
- Monthly/Yearly toggle (20% discount)
- FAQ accordion
- Referral program section
- CTA buttons

---

## 🎯 Career Pathing (`/career`)

**Tabs:**

### Analysis Tab
- Current level display (e.g., "Mid")
- Career progression timeline:
  - Junior (0-2 years, $60k-$90k)
  - Mid (2-5 years, $90k-$140k)
  - Senior (5-8 years, $140k-$200k)
  - Staff (8-12 years, $200k-$300k)
  - Principal (12+ years, $300k-$500k)
- Skill gaps with importance ratings
- Next milestone with requirements

### Goals Tab
- Target role input
- Target company (optional)
- Target salary
- Timeline (months)
- "Set Goal" button

### Recommendations Tab
- Personalized recommendations
- Priority badges (high/medium/low)
- Timeline estimates
- Salary trajectory chart

---

## 📈 Analytics Dashboard (`/analytics`)

**Stats Cards:**
1. **Total Applications** - Count + this month
2. **Interview Rate** - Percentage (color-coded by performance)
3. **Offer Rate** - Percentage + offers received
4. **Response Rate** - Percentage + avg response days

**Application Funnel:**
- Visual funnel showing conversion at each stage
- Percentage breakdown

**Market Insights:**
- Top hiring companies (top 10)
- Trending skills (tag cloud)
- Average salary by seniority level
- Remote work percentage

**Monthly Activity:**
- Bar chart: this month vs last month
- Growth rate indicator (↑/↓)

---

## 🏢 Company Reviews (`/reviews`)

**Layout:**

### Left Sidebar
- List of companies with reviews
- Shows: review count, average rating
- Click to view details

### Main Content
**Company Header:**
- Overall rating (large display)
- Category ratings:
  - Work-Life Balance
  - Culture
  - Compensation
  - Career Opportunities
  - Management

**Review Cards:**
- Title
- Pros/Cons sections
- Job title + employment status
- Rating stars
- Posted date

### Write Review Form
- Company name
- Overall rating (1-5 stars)
- Title
- Pros (textarea)
- Cons (textarea)
- Submit button

---

## 🎤 Interview Coach (`/interview-coach`)

**Start Screen:**
- Role selector dropdown
- Feature highlights
- "Start Mock Interview" button

**Interview Interface:**
- Chat-style conversation
- AI asks questions
- User types answers
- Real-time feedback scores:
  - Clarity
  - Technical depth
  - Structure

**End Screen:**
- Overall score (1-10)
- Strengths list
- Areas to improve
- Tips for next time
- "Practice Again" button

---

## 🔌 Chrome Extension

**Features:**
- Detects job pages on LinkedIn, Indeed, Glassdoor
- Floating "🚀 Apply with JobScale" button
- Popup with:
  - Login status
  - Job detection
  - Quick stats (applied, interviews, offers)
  - Dashboard link

**Installation:**
1. Go to `chrome://extensions/`
2. Enable Developer mode
3. Load unpacked → select `extension/` folder
4. Extension icon appears

---

## 📧 Automated Emails

**Sent automatically:**

1. **Welcome Email** - After registration
2. **Application Confirmation** - After applying
3. **Interview Notification** - When status changes
4. **Daily Job Alerts** - 9 AM, new matching jobs
5. **Weekly Summary** - Monday 8 AM, activity stats
6. **Follow-up Reminders** - 10 AM daily, old applications

---

## 💳 Billing Flow

**Checkout:**
1. User clicks "Upgrade" on pricing page
2. Creates Stripe checkout session
3. Redirected to Stripe hosted page
4. Enters payment details
5. Returns to success page
6. Subscription activated

**Webhooks:**
- `checkout.session.completed` → activate subscription
- `customer.subscription.deleted` → downgrade to free

**Usage Tracking:**
- Free tier: 5 applications/month limit
- Pro: unlimited
- Premium: unlimited + priority

---

## 🎯 User Journey Example

**Day 1:**
1. Land on homepage → Click "Get Started"
2. Register account → Welcome email sent
3. Complete profile (skills, preferences)
4. Upload resume → Auto-parsed
5. Browse jobs → See match scores
6. Apply to 3 jobs → AI tailors CV
7. Application confirmations sent

**Day 7:**
1. Daily job alert email → 5 new matches
2. Apply to 2 more jobs
3. Drag applications on kanban board
4. Check analytics → 20% interview rate

**Day 14:**
1. Interview notification email
2. Update application status to "Interviewing"
3. Use Interview Coach to practice
4. Check company reviews before interview

**Day 30:**
1. Receive offer → Update kanban to "Offer"
2. Weekly summary shows: 15 applications, 3 interviews, 1 offer
3. Refer a friend → Earn $10 credit
4. Consider upgrading to Pro for unlimited apps

---

## 🎨 Design System

**Colors:**
- Primary: Blue (#2563eb)
- Success: Green (#16a34a)
- Warning: Yellow (#f59e0b)
- Danger: Red (#dc2626)

**Components:**
- Navbar (consistent across pages)
- Cards (white background, shadow, rounded)
- Buttons (primary/secondary variants)
- Badges (color-coded status)
- Forms (labeled inputs, validation)

---

## 🔐 Security Features

- JWT authentication
- Password hashing (bcrypt)
- CORS protection
- SQL injection prevention (SQLAlchemy ORM)
- Input validation (Pydantic)
- Rate limiting ready

---

## 📱 Responsive Design

- Desktop-first approach
- Mobile-friendly layouts
- Touch-friendly buttons
- Responsive tables/cards

---

**This is what users experience when using JobScale!**
