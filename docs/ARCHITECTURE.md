# JobScale Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                           USER FACING                                │
├─────────────────────────────────────────────────────────────────────┤
│  Frontend (Next.js)     │  Mobile App (future)  │  Browser Extension│
│  - Job feed             │  - Push notifications │  - 1-click apply  │
│  - Application tracker  │  - Real-time updates  │  - Auto-fill      │
│  - CV builder           │                       │                   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          API LAYER                                   │
├─────────────────────────────────────────────────────────────────────┤
│  FastAPI Backend                                                     │
│  - Auth (JWT)           - Jobs API         - Applications API       │
│  - User profiles        - Search/filter    - AI services            │
│  - Rate limiting        - Pagination       - Webhooks               │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       BACKGROUND JOBS                                │
├─────────────────────────────────────────────────────────────────────┤
│  Celery Workers                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │ Job Scraping │  │ AI Processing│  │ Notifications & Emails   │   │
│  │ - Greenhouse │  │ - CV tailoring│  │ - Application updates    │   │
│  │ - Lever      │  │ - Matching    │  │ - Job alerts             │   │
│  │ - Workable   │  │ - Cover letters│ │ - Reminders              │   │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                                    │
├─────────────────────────────────────────────────────────────────────┤
│  PostgreSQL (primary)  │  Redis (cache/queue)  │  S3 (files)        │
│  - Users              │  - Session cache      │  - Resumes/PDFs    │
│  - Jobs (100k+)       │  - Rate limiting      │  - Tailored CVs    │
│  - Applications       │  - Task queue         │  - Cover letters   │
│  - Profiles           │  - Job cache          │                    │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Job Ingestion Pipeline

1. **Scheduler** triggers scrape every N hours per source
2. **Scrapers** fetch jobs from ATS providers
3. **Normalizer** standardizes format (title, location, salary, etc.)
4. **Deduplicator** removes duplicates (same job, multiple sources)
5. **Classifier** extracts skills, seniority, department
6. **Storage** saves to PostgreSQL
7. **Matcher** recalculates job-user fit scores

### Application Pipeline

1. User selects job or auto-match triggers
2. **AI Service** tailors CV to job description
3. **AI Service** generates cover letter
4. **Application** is created with status "draft"
5. User reviews (MVP) or auto-submits (future)
6. **Tracker** monitors status changes
7. **Notifications** alert user of updates

## Scaling Considerations

### Phase 1 (MVP - 0-1k users)
- Single PostgreSQL instance
- Basic Celery workers
- Simple matching algorithm
- Manual review before applying

### Phase 2 (Growth - 1k-10k users)
- Read replicas for DB
- Multiple worker queues (scraping, AI, notifications)
- Vector DB for semantic matching
- Caching layer (Redis) for job searches

### Phase 3 (Scale - 10k+ users)
- Sharded databases
- Dedicated scraping infrastructure (proxy rotation)
- ML-based matching model
- Real-time job alerts via WebSocket

## Security

- JWT authentication with refresh tokens
- Rate limiting per user/IP
- Encrypted passwords (bcrypt)
- HTTPS everywhere
- Input validation (Pydantic)
- SQL injection prevention (SQLAlchemy ORM)

## Monitoring

- Health check endpoints
- Structured logging (structlog)
- Error tracking (Sentry - TODO)
- Metrics (Prometheus - TODO)
