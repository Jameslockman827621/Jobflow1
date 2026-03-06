# JobScale - Job Engine Strategy

**The Core Differentiator:** Best job aggregation engine = Market dominance

---

## 🎯 CURRENT STATE

| Metric | Value | Status |
|--------|-------|--------|
| **Sources** | 2 (Greenhouse, Lever) | ⚠️ Limited |
| **Companies** | ~50 (Greenhouse only) | ⚠️ Tech-focused |
| **Jobs Indexed** | ~958 (from 5 companies tested) | ⚠️ Small |
| **Geography** | US + UK | ⚠️ Limited |
| **Industries** | Tech/Fintech | ⚠️ Narrow |
| **Update Frequency** | Every 6 hours | ✅ Good |
| **Freshness** | Jobs < 90 days | ✅ Good |

---

## 🚀 THE VISION: BEST JOB ENGINE

**Goal:** 100,000+ live jobs from 5,000+ companies across all industries, updated in real-time.

### **Competitive Landscape:**

| Platform | Est. Jobs | Sources | Industries | Geography |
|----------|-----------|---------|------------|-----------|
| **LinkedIn** | 20M+ | Direct postings | All | Global |
| **Indeed** | 50M+ | Aggregated | All | Global |
| **Glassdoor** | 5M+ | Direct + scraped | All | Global |
| **Otta** | 50K+ | Curated tech | Tech only | US/UK/EU |
| **Wellfound** | 100K+ | Startup direct | Tech/Startup | Global |
| **JobScale (current)** | ~1K | 2 ATS | Tech/Fintech | US/UK |
| **JobScale (target)** | 100K+ | 10+ sources | All | Global |

---

## 📊 MULTI-SOURCE STRATEGY

### **Tier 1: ATS Providers (High Quality, Easy)**

These provide structured APIs or clean HTML:

| Provider | Market Share | Companies | Jobs Est. | Implementation |
|----------|-------------|-----------|-----------|----------------|
| **Greenhouse** | ~30% | 4,000+ | 50K+ | ✅ Done (API) |
| **Lever** | ~15% | 2,000+ | 25K+ | ⚠️ HTML scrape |
| **Workable** | ~10% | 1,500+ | 15K+ | ❌ Not started |
| **Ashby** | ~5% | 500+ | 5K+ | ❌ Not started |
| **Greenhouse (Enterprise)** | ~5% | 500+ | 10K+ | ✅ Same API |

**Action Items:**
1. ✅ Greenhouse - Complete (50 companies, ~10K jobs potential)
2. ⚠️ Lever - Improve HTML parser, add 100 companies
3. ❌ Workable - Build scraper (API: `https://api.workable.com/sp/v1`)
4. ❌ Ashby - Build scraper (GraphQL API)

---

### **Tier 2: Job Aggregators (Medium Quality, API Access)**

| Source | API | Companies | Jobs Est. | Cost |
|--------|-----|-----------|-----------|------|
| **Google Jobs** | ❌ Scraping | All | 1M+ | Free |
| **JSearch API** | ✅ REST | All | 500K+ | $150/mo |
| **The Muse** | ✅ API | 500+ | 10K+ | Free tier |
| **Adzuna** | ✅ API | 50K+ | 500K+ | Free tier |
| **USAJobs** | ✅ API | US Gov | 50K+ | Free |
| **LinkedIn (via RapidAPI)** | ⚠️ Unofficial | All | 10M+ | $50/mo |

**Recommended:**
- **JSearch API** - Best coverage, affordable
- **Adzuna** - Free tier, good for EU
- **Google Jobs scraping** - Free but fragile

---

### **Tier 3: Direct Company Career Pages (High Effort, High Value)**

**Fortune 500 with custom career sites:**

| Company | Career Page | Jobs Est. | Difficulty |
|---------|-------------|-----------|------------|
| **Google** | careers.google.com | 5K+ | Medium |
| **Microsoft** | careers.microsoft.com | 10K+ | Medium |
| **Amazon** | amazon.jobs | 20K+ | Hard (anti-bot) |
| **Apple** | jobs.apple.com | 3K+ | Medium |
| **Meta** | meta.com/careers | 5K+ | Medium |
| **Netflix** | jobs.netflix.com | 500+ | Easy |
| **Salesforce** | salesforce.com/careers | 5K+ | Medium |

**Implementation:**
- Use Playwright for JavaScript-heavy sites
- Rotate proxies to avoid blocking
- Cache aggressively (scrape weekly, not daily)

---

### **Tier 4: Niche Job Boards (Industry-Specific)**

**By Industry:**

| Industry | Board | API | Jobs |
|----------|-------|-----|------|
| **Tech** | Stack Overflow Jobs | ✅ | 20K+ |
| **Tech** | HackerNews (Who's Hiring) | ❌ Scrape | 500/mo |
| **Remote** | We Work Remotely | ✅ | 5K+ |
| **Remote** | Remote OK | ✅ | 10K+ |
| **Startup** | Wellfound (AngelList) | ✅ | 50K+ |
| **Finance** | eFinancialCareers | ❌ | 50K+ |
| **Healthcare** | Health eCareers | ❌ | 100K+ |
| **Creative** | Behance | ✅ | 20K+ |
| **Non-profit** | Idealist | ✅ | 30K+ |

---

### **Tier 5: Government & Public Sector**

| Source | Geography | Jobs | API |
|--------|-----------|------|-----|
| **USAJobs** | US Federal | 50K+ | ✅ |
| **LinkedIn Public Sector** | Global | 100K+ | ❌ |
| **EU Careers** | European Union | 10K+ | ✅ |
| **UK Civil Service** | UK | 20K+ | ✅ |
| **Canada Jobs** | Canada | 30K+ | ✅ |

---

## 🛠️ TECHNICAL ARCHITECTURE

### **Current Architecture:**
```
┌─────────────────────────────────────────────┐
│            Celery Beat Scheduler            │
│  (scrape every 6 hours)                     │
└─────────────────┬───────────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
    ▼             ▼             ▼
┌────────┐   ┌────────┐   ┌────────┐
│Green-  │   │ Lever  │   │ Google │
│house   │   │ (HTML) │   │ Jobs   │
└───┬────┘   └───┬────┘   └───┬────┘
    │            │            │
    └────────────┼────────────┘
                 │
                 ▼
        ┌────────────────┐
        │  Job Model     │
        │  (PostgreSQL)  │
        └────────────────┘
```

### **Target Architecture:**
```
┌─────────────────────────────────────────────────────────┐
│              Job Ingestion Engine                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Scheduler  │  │   Priority   │  │   Rate       │ │
│  │   (Beat)     │  │   Queue      │  │   Limiter    │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                 │                 │          │
│         └─────────────────┼─────────────────┘          │
│                           │                            │
│         ┌─────────────────┼─────────────────┐          │
│         │                 │                 │          │
│         ▼                 ▼                 ▼          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  Tier 1     │  │  Tier 2     │  │  Tier 3     │    │
│  │  ATS (API)  │  │  Aggregators│  │  Direct     │    │
│  │  - Greenhouse│  │  - JSearch  │  │  - Google   │    │
│  │  - Lever    │  │  - Adzuna   │  │  - Company  │    │
│  │  - Workable │  │  - Indeed   │  │    Pages    │    │
│  │  - Ashby    │  │  - LinkedIn │  │  - Playwright│   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │
│         │                │                │            │
│         └────────────────┼────────────────┘            │
│                          │                             │
│                          ▼                             │
│                 ┌─────────────────┐                    │
│                 │  Normalizer     │                    │
│                 │  - Title        │                    │
│                 │  - Location     │                    │
│                 │  - Salary       │                    │
│                 │  - Seniority    │                    │
│                 │  - Remote flag  │                    │
│                 └────────┬────────┘                    │
│                          │                             │
│                          ▼                             │
│                 ┌─────────────────┐                    │
│                 │  Deduplication  │                    │
│                 │  - Fuzzy match  │                    │
│                 │  - URL hash     │                    │
│                 │  - Title+Company│                    │
│                 └────────┬────────┘                    │
│                          │                             │
│                          ▼                             │
│                 ┌─────────────────┐                    │
│                 │  Enrichment     │                    │
│                 │  - Salary est.  │                    │
│                 │  - Skills extract│                   │
│                 │  - Remote score │                    │
│                 │  - Company info │                    │
│                 └────────┬────────┘                    │
│                          │                             │
│                          ▼                             │
│                 ┌─────────────────┐                    │
│                 │  Job Model      │                    │
│                 │  (PostgreSQL)   │                    │
│                 └─────────────────┘                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 IMPLEMENTATION ROADMAP

### **Phase 1: Scale ATS Coverage (Week 1-2)**

**Goal:** 500 companies, 50K jobs

| Task | Effort | Impact |
|------|--------|--------|
| Expand Greenhouse list to 200 companies | 2h | High |
| Improve Lever HTML parser | 4h | Medium |
| Add Workable scraper | 8h | High |
| Add Ashby scraper | 8h | Medium |
| Company research (find ATS providers) | 4h | High |

**Companies to Add (Greenhouse):**
- All YC companies (check yc.com/companies)
- All tech unicorns (Forbes Cloud 100)
- All remote-first companies (Owl Labs list)

---

### **Phase 2: Add Aggregators (Week 2-3)**

**Goal:** +50K jobs from APIs

| Task | Effort | Impact |
|------|--------|--------|
| Integrate JSearch API | 4h | Very High |
| Integrate Adzuna API | 4h | High |
| Integrate USAJobs API | 2h | Medium |
| Integrate The Muse API | 2h | Low |

**Cost:** ~$150/mo for JSearch Pro plan

---

### **Phase 3: Direct Scraping (Week 3-4)**

**Goal:** +100K jobs from top companies

| Task | Effort | Impact |
|------|--------|--------|
| Build Playwright scraper framework | 8h | High |
| Add Fortune 50 career pages (top 50) | 20h | Very High |
| Proxy rotation setup | 4h | High |
| CAPTCHA solving (2Captcha) | 4h | Medium |

**Target Companies:**
- FAANG (Google, Apple, Amazon, Netflix, Meta)
- Microsoft, Salesforce, Oracle, IBM
- Banks (JPMorgan, Goldman, Morgan Stanley)
- Consulting (McKinsey, BCG, Bain)

---

### **Phase 4: Niche Boards (Week 4-5)**

**Goal:** +50K jobs from specialized sources

| Task | Effort | Impact |
|------|--------|--------|
| Stack Overflow Jobs API | 4h | High |
| Wellfound (AngelList) API | 4h | High |
| We Work Remotely API | 2h | Medium |
| Remote OK API | 2h | Medium |
| Idealist (non-profit) | 2h | Low |
| Behance (creative) | 4h | Low |

---

### **Phase 5: Global Expansion (Week 5-6)**

**Goal:** Non-US/UK coverage

| Region | Source | Jobs | Effort |
|--------|--------|------|--------|
| **EU** | EU Careers | 10K+ | 4h |
| **EU** | LinkedIn EU | 500K+ | API |
| **Canada** | Job Bank | 50K+ | 4h |
| **Australia** | Seek | 100K+ | 8h |
| **India** | Naukri | 200K+ | 8h |
| **Singapore** | MyCareersFuture | 30K+ | 4h |

---

### **Phase 6: Real-Time Updates (Week 6-7)**

**Goal:** Jobs updated within 1 hour of posting

| Task | Effort | Impact |
|------|--------|--------|
| Implement webhooks (where available) | 8h | High |
| RSS feed monitoring | 4h | Medium |
| Change detection (Diffbot) | 4h | Medium |
| Priority queue for hot companies | 4h | Medium |

---

## 🔍 DATA QUALITY & ENRICHMENT

### **Normalization Pipeline:**

```python
class JobNormalizer:
    def normalize(self, raw_job: Dict) -> Job:
        # Title standardization
        job.title = self.standardize_title(raw_job.title)
        # e.g., "SWE II" → "Software Engineer II"
        
        # Location parsing
        job.city, job.state, job.country = self.parse_location(raw_job.location)
        
        # Remote detection
        job.remote = self.detect_remote(raw_job.description)
        job.hybrid = self.detect_hybrid(raw_job.description)
        
        # Salary extraction
        job.min_salary, job.max_salary = self.parse_salary(raw_job.salary_text)
        
        # Seniority extraction
        job.seniority = self.extract_seniority(raw_job.title, raw_job.description)
        
        # Skills extraction
        job.skills = self.extract_skills(raw_job.description)
        
        return job
```

### **Deduplication Strategy:**

```python
def is_duplicate(new_job: Job, existing_jobs: List[Job]) -> bool:
    # Exact match on external_id + source
    if any(j.external_id == new_job.external_id and j.source == new_job.source 
           for j in existing_jobs):
        return True
    
    # Fuzzy match on title + company + location
    for job in existing_jobs:
        if (fuzzy_match(job.title, new_job.title, threshold=0.9) and
            fuzzy_match(job.company, new_job.company, threshold=0.95) and
            fuzzy_match(job.location, new_job.location, threshold=0.9)):
            return True
    
    return False
```

### **Enrichment Services:**

| Enrichment | Source | Cost |
|------------|--------|------|
| **Salary estimation** | Levels.fyi API | Free |
| **Company info** | Clearbit API | Free tier |
| **Skills extraction** | spaCy NLP | Free |
| **Remote score** | Custom ML model | Free |
| **Tech stack** | BuiltWith API | $299/mo |

---

## 📊 SCALING METRICS

### **Target by Phase:**

| Phase | Companies | Jobs | Update Frequency | Coverage |
|-------|-----------|------|------------------|----------|
| **Current** | 50 | 1K | 6 hours | US/UK Tech |
| **Phase 1** | 500 | 50K | 6 hours | US/UK Tech |
| **Phase 2** | 1,000 | 100K | 3 hours | US/UK All |
| **Phase 3** | 2,000 | 200K | 1 hour | Global Tech |
| **Phase 4** | 3,000 | 300K | 1 hour | Global All |
| **Phase 5** | 5,000 | 500K | Real-time | Global All |

---

## 💰 COST ANALYSIS

### **Monthly Operating Costs:**

| Service | Tier | Cost | Jobs Covered |
|---------|------|------|--------------|
| **JSearch API** | Pro | $150/mo | 500K+ |
| **Adzuna API** | Free | $0 | 100K+ |
| **Proxy Service** | Smartproxy | $75/mo | Unlimited |
| **2Captcha** | Pay-per-use | $50/mo | Unlimited |
| **Server (scraping)** | 4x CPU | $200/mo | Unlimited |
| **Total** | | **$475/mo** | **600K+ jobs** |

### **Cost Per Job:**
- **Current:** ~$0.50/job (1K jobs / $475)
- **Target:** ~$0.001/job (500K jobs / $475)

---

## 🛡️ ANTI-BLOCKING STRATEGIES

### **For Direct Scraping:**

1. **User-Agent Rotation**
   ```python
   user_agents = [
       "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
       "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15",
       # ... 100+ more
   ]
   ```

2. **IP Rotation (Proxy Service)**
   - Smartproxy: 40M+ residential IPs
   - Rotate every request
   - Geographic targeting

3. **Rate Limiting**
   ```python
   @celery_app.task(rate_limit="10/m")
   def scrape_company(company: str):
       # Max 10 requests per minute per company
   ```

4. **Headless Browser (Playwright)**
   - Execute JavaScript
   - Simulate human behavior
   - Bypass basic bot detection

5. **CAPTCHA Solving**
   - 2Captcha API integration
   - Fallback when detected

---

## 🎯 COMPETITIVE ADVANTAGES

### **What Makes JobScale Different:**

| Feature | LinkedIn | Indeed | JobScale |
|---------|----------|--------|----------|
| **AI-tailored applications** | ❌ | ❌ | ✅ |
| **Match score** | ❌ | ❌ | ✅ (77% accuracy) |
| **Application tracking** | ❌ | ❌ | ✅ (Kanban) |
| **Career pathing** | ❌ | ❌ | ✅ |
| **Company reviews** | ✅ | ❌ | ✅ |
| **Interview prep** | ❌ | ❌ | ✅ |
| **Salary negotiation** | ❌ | ❌ | ✅ |
| **Job coverage** | 20M+ | 50M+ | 500K+ (target) |

**Key Insight:** We don't need MORE jobs than LinkedIn. We need SMARTER job matching + application automation.

---

## 📋 IMMEDIATE ACTION ITEMS

### **This Week (Priority 1):**

1. **Expand Greenhouse company list** (2h)
   - Research 150 more companies
   - Update `backend/app/scrapers/companies.py`

2. **Integrate JSearch API** (4h)
   - Sign up for API key
   - Add scraper: `backend/app/scrapers/jsearch.py`
   - Test with 10 sample searches

3. **Improve Lever scraper** (4h)
   - Fix HTML parsing issues
   - Add 50 more Lever companies

4. **Add Workable scraper** (8h)
   - API docs: https://api.workable.com/sp/v1
   - Create: `backend/app/scrapers/workable.py`
   - Test with 10 companies

### **Next Week (Priority 2):**

5. **Build Playwright framework** (8h)
   - Base scraper class for JS-heavy sites
   - Proxy integration
   - Screenshot on failure (debugging)

6. **Add Fortune 50 career pages** (16h)
   - Start with top 20 companies
   - Custom parser for each

7. **Implement deduplication** (4h)
   - Fuzzy matching on title+company
   - URL hash comparison

---

## 📈 SUCCESS METRICS

### **KPIs to Track:**

| Metric | Current | Target (30d) | Target (90d) |
|--------|---------|--------------|--------------|
| **Total jobs** | 1K | 50K | 200K |
| **Companies** | 50 | 500 | 2,000 |
| **Sources** | 2 | 5 | 10 |
| **Freshness (<7d)** | 80% | 90% | 95% |
| **Geographic coverage** | 2 countries | 5 countries | 20 countries |
| **Industry coverage** | Tech/Fintech | +Healthcare, Retail | All |
| **Update frequency** | 6 hours | 3 hours | 1 hour |

---

## 🎯 CONCLUSION

**The best job engine = Breadth + Depth + Freshness**

| Dimension | Strategy |
|-----------|----------|
| **Breadth** | 10+ sources (ATS, aggregators, direct) |
| **Depth** | 500K+ jobs, all industries, global |
| **Freshness** | Real-time updates, <1 hour latency |
| **Quality** | Normalized, deduplicated, enriched |

**Investment:** ~$500/mo + 40 hours dev time  
**Return:** Best job database in market → User acquisition → Revenue

---

**Ready to start with Phase 1 this week?**
