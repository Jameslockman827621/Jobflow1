# JobScale Deployment Guide

Complete guide to deploying JobScale to production.

---

## 🚀 Quick Deploy (Docker)

### Prerequisites
- Docker & Docker Compose
- Domain name (optional)
- SSL certificate (Let's Encrypt)

### 1. Clone & Configure

```bash
cd /home/admin/.openclaw/workspace
cp backend/.env.example backend/.env
```

Edit `backend/.env`:

```env
# Production settings
DEBUG=false
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=postgresql://user:pass@db:5432/jobscale
REDIS_URL=redis://redis:6379/0

# Email (SendGrid)
SENDGRID_API_KEY=sg.xxx

# AI (OpenAI)
OPENAI_API_KEY=sk-xxx
LLM_MODEL=gpt-4-turbo-preview

# Stripe
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# CORS
CORS_ORIGINS=["https://jobscale.com"]
```

### 2. Start Services

```bash
cd infra
docker-compose up -d
```

### 3. Initialize Database

```bash
docker-compose exec backend python scripts/init_db.py
```

### 4. Verify

- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Kanban: http://localhost:3000/kanban
- Pricing: http://localhost:3000/pricing

---

## 🏗️ Production Architecture

```
                    ┌─────────────┐
                    │   CloudFl   │
                    │   (CDN)     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Nginx     │
                    │  (Reverse   │
                    │   Proxy)    │
                    └──┬─────┬────┘
                       │     │
         ┌─────────────┘     └─────────────┐
         │                                 │
┌────────▼────────┐              ┌────────▼────────┐
│   Frontend      │              │   Backend       │
│   (Next.js)     │              │   (FastAPI)     │
│   Port 3000     │              │   Port 8000     │
└────────┬────────┘              └────────┬────────┘
         │                                │
         └────────────┬───────────────────┘
                      │
         ┌────────────▼────────────┐
         │    PostgreSQL + Redis   │
         │    (RDS/ElastiCache)    │
         └─────────────────────────┘
                      │
         ┌────────────▼────────────┐
         │    Celery Workers       │
         │    (Job Scraping)       │
         └─────────────────────────┘
```

---

## ☁️ Deploy to AWS

### 1. ECS + RDS Setup

```bash
# Create RDS PostgreSQL
aws rds create-db-instance \
  --db-instance-identifier jobscale-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --master-username postgres \
  --master-user-password YOUR_PASSWORD \
  --allocated-storage 100

# Create ElastiCache Redis
aws elasticache create-cache-cluster \
  --cache-cluster-id jobscale-redis \
  --engine redis \
  --cache-node-type cache.t3.medium \
  --num-cache-nodes 1
```

### 2. Build & Push Docker Images

```bash
# Backend
docker build -t your-ecr-repo/jobscale-backend ./backend
docker push your-ecr-repo/jobscale-backend

# Frontend
docker build -t your-ecr-repo/jobscale-frontend ./frontend
docker push your-ecr-repo/jobscale-frontend
```

### 3. Deploy to ECS

Use the provided `infra/aws-ecs-task-definition.json` (create from template).

---

## 🚀 Deploy to Railway/Render (Easier)

### Railway

1. Connect GitHub repo
2. Add services:
   - PostgreSQL (auto-provisioned)
   - Redis (auto-provisioned)
   - Web service (backend)
   - Web service (frontend)
   - Worker service (Celery)
3. Set environment variables
4. Deploy!

### Render

```yaml
# render.yaml
services:
  - type: web
    name: jobscale-backend
    env: python
    buildCommand: pip install -r backend/requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0
    
  - type: web
    name: jobscale-frontend
    env: node
    buildCommand: cd frontend && npm install && npm run build
    startCommand: cd frontend && npm start
    
  - type: worker
    name: jobscale-worker
    env: python
    buildCommand: pip install -r backend/requirements.txt
    startCommand: celery -A app.tasks.celery_app worker
    
  - type: pserv
    name: jobscale-db
    plan: starter
    database: postgresql
```

---

## 📊 Monitoring

### Health Checks

- `GET /api/v1/health/` - Basic health
- `GET /api/v1/health/ready` - DB connection check

### Logging

Structured logs with structlog. View with:

```bash
docker-compose logs -f backend
docker-compose logs -f worker
```

### Metrics (Prometheus)

Add to `backend/requirements.txt`:
```
prometheus-client==0.19.0
prometheus-fastapi-instrumentator==6.1.0
```

---

## 🔐 Security Checklist

- [ ] Change `SECRET_KEY` in production
- [ ] Use HTTPS everywhere
- [ ] Enable CORS only for your domain
- [ ] Set `DEBUG=false`
- [ ] Use environment variables for secrets
- [ ] Enable database SSL
- [ ] Set up firewall rules
- [ ] Enable automatic security updates
- [ ] Set up backup strategy
- [ ] Configure rate limiting

---

## 💾 Database Migrations

Using Alembic:

```bash
cd backend
alembic init alembic
# Edit alembic.ini with DATABASE_URL
alembic revision --autogenerate -m "Initial"
alembic upgrade head
```

---

## 📧 Email Configuration

### SendGrid

1. Sign up at sendgrid.com
2. Create API key
3. Add to `.env`: `SENDGRID_API_KEY=sg.xxx`
4. Update `backend/app/services/email.py` to use SendGrid SDK

### SMTP (Gmail)

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASSWORD=your-app-password
```

---

## 💳 Stripe Setup

1. Create Stripe account
2. Get API keys from Dashboard
3. Create products & prices:
   - Pro Monthly: `price_pro_monthly`
   - Pro Yearly: `price_pro_yearly`
   - Premium Monthly: `price_premium_monthly`
4. Add webhook endpoint: `https://yourdomain.com/api/v1/billing/webhook`
5. Subscribe to events: `checkout.session.completed`, `customer.subscription.deleted`

---

## 🔄 CI/CD (GitHub Actions)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build & Deploy
        run: |
          docker-compose build
          docker-compose up -d
```

---

## 📈 Scaling

### Horizontal Scaling

- Add more Celery workers
- Use read replicas for PostgreSQL
- Add Redis Cluster
- Use load balancer

### Caching

- Cache job search results (5 min)
- Cache match scores (1 hour)
- Cache user profiles (10 min)

### Rate Limiting

Add to FastAPI:
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
```

---

## 🆘 Troubleshooting

### Backend won't start
```bash
docker-compose logs backend
# Check DATABASE_URL is correct
# Check all dependencies installed
```

### Celery tasks not running
```bash
docker-compose logs worker
# Check Redis is accessible
# Check task imports in celery_app
```

### Frontend can't connect to API
```bash
# Check NEXT_PUBLIC_API_URL in frontend/.env.local
# Check CORS_ORIGINS in backend/.env
```

---

## 📞 Support

- Docs: `/docs` (Swagger UI)
- Issues: GitHub Issues
- Email: support@jobscale.com
