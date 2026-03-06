# Deploy JobScale to Production

Step-by-step instructions to get your SaaS live.

---

## Option 1: Railway (Easiest - 15 minutes)

### Step 1: Create Railway Account
1. Go to https://railway.app
2. Sign up with GitHub
3. Click "New Project"

### Step 2: Deploy Database
1. Click "New" → "Database" → "PostgreSQL"
2. Wait for provisioning
3. Copy the `DATABASE_URL` from Variables tab

### Step 3: Deploy Redis
1. Click "New" → "Database" → "Redis"
2. Copy the `REDIS_URL` from Variables tab

### Step 4: Deploy Backend
1. Click "New" → "GitHub Repo"
2. Select your JobScale repo
3. Add environment variables:
   ```
   DATABASE_URL=postgresql://...
   REDIS_URL=redis://...
   SECRET_KEY=your-random-secret-key
   OPENAI_API_KEY=sk-...
   DEBUG=false
   CORS_ORIGINS=["https://your-domain.railway.app"]
   ```
4. Set Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Set Root Directory: `backend`
6. Deploy!

### Step 5: Deploy Frontend
1. Click "New" → "GitHub Repo"
2. Select your JobScale repo
3. Add environment variable:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend.railway.app/api/v1
   ```
4. Set Build Command: `npm run build`
5. Set Start Command: `npm start`
6. Set Root Directory: `frontend`
7. Deploy!

### Step 6: Configure Domain (Optional)
1. Go to Project Settings → Domains
2. Add custom domain
3. Update DNS records as instructed

**Total cost:** ~$20/month (database + redis + compute)

---

## Option 2: Render (Also Easy - 20 minutes)

### Step 1: Create Render Account
1. Go to https://render.com
2. Sign up with GitHub

### Step 2: Create PostgreSQL
1. New → "PostgreSQL"
2. Choose free tier
3. Copy connection string

### Step 3: Create Web Service (Backend)
1. New → "Web Service"
2. Connect repo
3. Configuration:
   - Root Directory: `backend`
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables (same as Railway)
5. Deploy

### Step 4: Create Web Service (Frontend)
1. New → "Web Service"
2. Connect repo
3. Configuration:
   - Root Directory: `frontend`
   - Build: `npm install && npm run build`
   - Start: `npm start`
4. Add environment variable: `NEXT_PUBLIC_API_URL`
5. Deploy

**Total cost:** Free tier available, ~$25/month for production

---

## Option 3: Vercel + Supabase (Modern Stack - 25 minutes)

### Step 1: Supabase Database
1. Go to https://supabase.com
2. Create new project
3. Copy connection string

### Step 2: Vercel Frontend
1. Go to https://vercel.com
2. Import GitHub repo
3. Set Root Directory: `frontend`
4. Add environment variables
5. Deploy (automatic HTTPS)

### Step 3: Deploy Backend (use Railway for backend)
- Vercel is frontend-only for this setup
- Deploy backend to Railway following Option 1

**Total cost:** Free tier generous, ~$20/month for production

---

## Option 4: AWS (Full Control - 1 hour)

### Services Needed:
- ECS Fargate (backend + frontend)
- RDS PostgreSQL
- ElastiCache Redis
- Application Load Balancer
- Route53 (domain)
- Certificate Manager (SSL)

### Steps:
1. Create RDS PostgreSQL instance
2. Create ElastiCache Redis cluster
3. Build Docker images → push to ECR
4. Create ECS task definitions
5. Create ECS services
6. Configure ALB
7. Set up domain + SSL
8. Update environment variables

**Total cost:** ~$100/month (overkill for MVP)

---

## Post-Deployment Checklist

### Database Setup
```bash
# Connect to your deployed backend
curl https://your-backend.com/api/v1/health

# Initialize database tables
# (Run migration script or use Alembic)
```

### Environment Variables to Set:

**Backend:**
```env
DATABASE_URL=postgresql://user:pass@host:5432/jobscale
REDIS_URL=redis://host:6379
SECRET_KEY=generate-random-32-chars
OPENAI_API_KEY=sk-...
STRIPE_SECRET_KEY=sk_live_...
SENDGRID_API_KEY=SG....
DEBUG=false
CORS_ORIGINS=["https://your-domain.com"]
```

**Frontend:**
```env
NEXT_PUBLIC_API_URL=https://your-backend.com/api/v1
```

### Test Everything:
- [ ] User registration works
- [ ] Login works
- [ ] Profile save works
- [ ] Job scraping triggers
- [ ] Applications create
- [ ] Emails send (check spam folder)
- [ ] Stripe checkout works (test mode)
- [ ] Analytics load
- [ ] Reviews submit

### Stripe Setup:
1. Create products in Stripe Dashboard
2. Copy price IDs to `backend/app/api/billing.py`
3. Set webhook endpoint: `https://your-backend.com/api/v1/billing/webhook`
4. Subscribe to events: `checkout.session.completed`, `customer.subscription.deleted`

### Email Setup:
1. Sign up at SendGrid
2. Verify domain
3. Create API key
4. Add to environment variables

### Monitoring:
1. Set up health check alerts
2. Configure log aggregation (Papertrail, Datadog)
3. Set up error tracking (Sentry)

---

## Quick Local Test (Before Deploying)

```bash
# In workspace
cd infra
docker-compose up -d

# Test locally first
open http://localhost:3000
open http://localhost:8000/docs

# If it works locally, it'll work in production
```

---

## Need Help?

- Check `DEPLOYMENT.md` for detailed architecture
- Check logs: `docker-compose logs -f`
- API docs: `http://localhost:8000/docs`

---

**You're ready to deploy! 🚀**
