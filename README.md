# JobScale

AI-powered job search and career acceleration platform.

## Thesis

There are millions of job openings across thousands of companies. Most people manually apply to <10 jobs. JobScale automatically finds, matches, and applies to relevant positions - then continues searching for better opportunities even after you're employed.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Frontend   │────▶│   Backend    │────▶│  Database   │
│  (Next.js)  │     │  (FastAPI)   │     │ (PostgreSQL)│
└─────────────┘     └──────────────┘     └─────────────┘
                          │
                          ▼
                   ┌──────────────┐
                   │   Scrapers   │
                   │ - Greenhouse │
                   │ - Lever      │
                   │ - Workable   │
                   └──────────────┘
```

## Tech Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy
- **Frontend:** Next.js 14, React, TypeScript, Tailwind
- **Database:** PostgreSQL 16
- **Cache/Queue:** Redis 7, Celery
- **AI:** OpenAI API (planned)

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+ (for local frontend dev)
- Python 3.12+ (for local backend dev)

### Run with Docker

```bash
cd infra
docker-compose up -d
```

Services:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### Local Development

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI routes
│   │   ├── core/          # Config, security
│   │   ├── models/        # SQLAlchemy models
│   │   ├── scrapers/      # Job source scrapers
│   │   ├── services/      # Business logic
│   │   ├── ai/            # LLM integration
│   │   └── tasks/         # Celery tasks
│   └── requirements.txt
├── frontend/
│   ├── src/app/           # Next.js pages
│   ├── src/components/
│   └── package.json
├── infra/
│   └── docker-compose.yml
└── docs/
```

## MVP Features

1. **Job Aggregation**
   - Scrape Greenhouse, Lever, Workable ATS systems
   - Normalize and deduplicate jobs
   - Store in searchable database

2. **User Profiles**
   - Skills, experience, preferences
   - Resume parsing
   - Salary/location preferences

3. **Matching**
   - Semantic job-user matching
   - Score jobs by fit

4. **Application Assistant**
   - Tailor CV per job
   - Generate cover letters
   - Track applications

## Roadmap

- [ ] Complete user auth (JWT)
- [ ] Implement job scrapers with scheduling
- [ ] Build matching algorithm
- [ ] AI CV tailoring
- [ ] Application tracking dashboard
- [ ] Email notifications
- [ ] Browser extension for 1-click apply

## Legal Notes

- Scraping ATS providers (Greenhouse, Lever, Workable) is generally acceptable - they're designed for embedding
- Avoid direct LinkedIn scraping for production SaaS (ToS violation)
- Use official APIs where available
- Respect rate limits and robots.txt

## License

Private - All rights reserved
