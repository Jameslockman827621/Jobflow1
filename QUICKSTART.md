# JobScale Quick Start

## Prerequisites

- Docker & Docker Compose
- Python 3.12+
- Node.js 20+

## Option 1: Docker (Recommended)

```bash
cd infra
docker-compose up -d
```

Wait for services to start, then:
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Option 2: Local Development

### 1. Start Database & Redis

```bash
cd infra
docker-compose up -d db redis
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Initialize database
cd scripts
python init_db.py
cd ..

# Start backend
uvicorn app.main:app --reload
```

Backend API: http://localhost:8000

### 3. Start Celery Worker (optional, for background jobs)

```bash
cd backend
source venv/bin/activate
celery -A app.tasks.celery_app worker --loglevel=info
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend: http://localhost:3000

## Test the API

```bash
# Register a user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123","first_name":"Test","last_name":"User"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=password123"

# Trigger job scraping
curl -X POST http://localhost:8000/api/v1/jobs/scrape/greenhouse
```

## Test Scrapers Manually

```bash
cd backend/scripts
python scrape_jobs.py
```

## Configure AI (Optional)

Edit `backend/.env`:

```
OPENAI_API_KEY=sk-your-key-here
LLM_MODEL=gpt-4-turbo-preview
```

This enables AI-powered CV tailoring and cover letter generation.

## Next Steps

1. Register an account at http://localhost:3000/login
2. Trigger job scraping via API docs
3. Browse jobs and apply
4. Check applications tab
