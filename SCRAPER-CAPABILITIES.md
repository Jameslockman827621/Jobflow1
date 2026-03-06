# Job Scraper Capabilities Analysis

## LinkedIn Jobs Scraper (Apify Actor: hKByXkMQaC5Qt9UMN)

### Supported Parameters:

| Parameter | Type | Values | Description |
|-----------|------|--------|-------------|
| `keywords` | string | Any | Job title/keywords to search for |
| `location` | string | Any | Geographic location (city, country, region) |
| `max_jobs` | int | 1-1000 | Maximum jobs to scrape |
| `date_posted` | string | `anytime`, `month`, `week`, `day` | Time filter |
| `job_type` | string | `fulltime`, `parttime`, `contract`, `internship` | Employment type |
| `remote` | boolean | `true`, `false` | Include remote jobs |

### Data Returned:

| Field | Type | Coverage | Description |
|-------|------|----------|-------------|
| `title` | string | 100% | Job title |
| `companyName` | string | 100% | Company name |
| `location` | string | 100% | Job location |
| `link` | string | 100% | Job URL |
| `description` | string | 100% | Full job description |
| `postedAt` | date | 100% | Posting date |
| `seniorityLevel` | string | 99% | Entry/Mid/Senior/Lead/Executive |
| `employmentType` | string | 100% | Full-time/Part-time/etc. |
| `jobFunction` | string | 99% | Department/function |
| `industries` | string | 99% | Industry categories |
| `applicantsCount` | int | 100% | Number of applicants |
| `companyLogo` | string | 100% | Company logo URL |
| `companyDescription` | string | 100% | Company description |
| `companyEmployeesCount` | int | 98% | Company size |
| `companyWebsite` | string | 97% | Company website |
| `salaryInfo` | string | 19% | Salary information (if available) |
| `benefits` | array | 54% | Listed benefits |
| `applyUrl` | string | 60% | Direct application URL |
| `jobPosterName` | string | 30% | Recruiter/hiring manager name |
| `jobPosterProfileUrl` | string | 30% | LinkedIn profile of poster |

### Limitations:
- ❌ No salary filtering (LinkedIn rarely shows salaries)
- ❌ No experience level filtering in search (only in results)
- ❌ No company size filtering
- ❌ No industry filtering in search
- ⚠️ Remote filter is boolean (can't filter for remote-only)

---

## Indeed Jobs Scraper (Apify Actor: MXLpngmVpE8WTESQr)

### Supported Parameters:

| Parameter | Type | Values | Description |
|-----------|------|--------|-------------|
| `country` | string | `us`, `uk`, `ca`, `au`, `de`, `fr`, `ie`, `nl`, `in`, `sg` | Country code |
| `query` | string | Any | Job search query |
| `location` | string | Any | City/region name |
| `maxRows` | int | 1-10000 | Maximum jobs to scrape |
| `remote` | string | `remote`, `hybrid`, `null` | Remote work filter |
| `jobType` | string | `fulltime`, `parttime`, `contract`, `internship`, `temporary` | Employment type |
| `fromDays` | int | 1-30 | Days since posting (1-30) |
| `sort` | string | `relevance`, `date` | Sort order |
| `level` | string | `entry_level`, `mid_level`, `senior_level`, `director`, `executive` | Seniority level |
| `urls` | array | Indeed URLs | Specific company/job URLs to scrape |
| `maxRowsPerUrl` | int | 1-1000 | Max jobs per URL |
| `enableUniqueJobs` | boolean | `true`, `false` | Deduplicate results |
| `includeSimilarJobs` | boolean | `true`, `false` | Include similar roles |

### Data Returned:

| Field | Type | Coverage | Description |
|-------|------|----------|-------------|
| `title` | string | 100% | Job title |
| `companyName` | string | 100% | Company name |
| `location` | object | 100% | Structured location (city, country, lat/lng) |
| `jobUrl` | string | 100% | Job URL |
| `descriptionText` | string | 100% | Plain text description |
| `descriptionHtml` | string | 100% | HTML description |
| `datePublished` | date | 100% | Publication date |
| `salary` | object | 20% | Structured salary (min, max, currency, text) |
| `jobType` | string | 100% | Full-time/Part-time/etc. |
| `isRemote` | boolean | 100% | Remote flag |
| `attributes` | array | 100% | Job features (remote, hybrid, etc.) |
| `companyDescription` | string | 60% | Company description |
| `companyLogoUrl` | string | 60% | Company logo |
| `companyUrl` | string | 100% | Company website |
| `companyIndustry` | string | 40% | Industry |
| `companyNumEmployees` | int | 60% | Company size |
| `companyRevenue` | string | 60% | Revenue range |
| `companyFounded` | int | 60% | Founding year |
| `rating` | float | 100% | Company rating (1-5) |
| `benefits` | array | 40% | Employee benefits |
| `emails` | array | 40% | Contact emails |
| `hiringDemand` | string | 100% | Hiring urgency indicator |

### Limitations:
- ⚠️ Salary only available for ~20% of jobs
- ❌ No direct company filtering (unless using URLs)
- ❌ No specific skills filtering

---

## Comparison & Recommendations

### Parameters Both Support:
✅ Job title/keywords  
✅ Location  
✅ Job type (fulltime, parttime, contract, etc.)  
✅ Remote/hybrid  
✅ Date posted (LinkedIn: day/week/month, Indeed: 1-30 days)  
✅ Max results  

### Indeed-Only Parameters:
🎯 **Country selection** (10 countries)  
🎯 **Seniority level** (entry, mid, senior, director, executive)  
🎯 **Sort order** (relevance, date)  
🎯 **Specific URLs** (scrape company pages directly)  

### LinkedIn-Only Parameters:
🎯 **Boolean remote** (include/exclude remote)  

### Data Quality Comparison:

| Aspect | LinkedIn | Indeed | Winner |
|--------|----------|--------|--------|
| **Salary data** | 19% | 20% | Tie |
| **Company info** | Excellent | Good | LinkedIn |
| **Job description** | Full | Full | Tie |
| **Location accuracy** | Good | Excellent (structured) | Indeed |
| **Seniority data** | 99% | Extracted | LinkedIn |
| **Applicant count** | ✅ Yes | ❌ No | LinkedIn |
| **Company ratings** | ❌ No | ✅ Yes | Indeed |
| **Hiring urgency** | ❌ No | ✅ Yes | Indeed |
| **Contact info** | Job poster only | Emails available | Indeed |

---

## Recommended Onboarding Fields

Based on scraper capabilities, here's what we should collect:

### Essential (Both Scrapers):
1. ✅ **Job titles/roles** (multi-select + custom)
2. ✅ **Locations** (multi-select with country)
3. ✅ **Remote preference** (Remote only, Hybrid, On-site, Any)
4. ✅ **Job type** (Full-time, Part-time, Contract, Internship)
5. ✅ **Date posted** (Last 24h, Week, Month, Any time)

### Indeed-Specific (High Value):
6. ✅ **Seniority level** (Entry, Mid, Senior, Director, Executive)
7. ✅ **Country** (UK, US, Canada, Australia, Germany, France, etc.)

### LinkedIn-Specific (Medium Value):
8. ⚠️ **Company size preference** (Startup, Mid, Enterprise) - from company data
9. ⚠️ **Industry preference** (Tech, Finance, Healthcare, etc.) - from job function

### Nice to Have:
10. ⚠️ **Salary expectations** (min/max) - for filtering, not search
11. ⚠️ **Target companies** (for Greenhouse/Lever direct scraping)
12. ⚠️ **Skills** (for matching, not search)

---

## Optimal Search Strategy

### For Each User Search:

```
1. Indeed Search (FAST - 30s)
   - Use: query, location, country, remote, jobType, level, fromDays
   - Get: 30-50 jobs per search

2. LinkedIn Search (SLOWER - 100s)
   - Use: keywords, location, date_posted, job_type, remote
   - Get: 50-100 jobs per search

3. Greenhouse/Lever (TARGETED - 60s)
   - Use: target_companies list
   - Get: Direct ATS jobs

4. Deduplicate → Cache → Return
```

### Search Combinations:

**Per user onboarding, run:**
- 2-3 role searches × 2-3 locations = 4-9 searches per source
- Total: ~16-36 searches
- Expected results: 100-300 jobs (before deduplication)
- After deduplication: 50-150 unique jobs

---

## Updated Onboarding Flow Recommendation

### Step 1: Role & Seniority
- Job titles (multi-select from 50+ common roles + custom)
- Seniority level (Entry, Mid, Senior, Lead, Director, Executive)

### Step 2: Location & Remote
- Countries (UK, US, Canada, Australia, EU, etc.)
- Cities/Regions (London, New York, Remote, etc.)
- Remote preference (Remote only, Hybrid OK, On-site only)

### Step 3: Job Type & Timing
- Employment type (Full-time, Part-time, Contract, Internship)
- Date posted (Last 24h, Week, Month, Any)

### Step 4: Companies & Salary (Optional)
- Target companies (for direct ATS scraping)
- Minimum salary expectation
- Industry preferences

### Step 5: Review & Search
- Show summary
- Run searches (2-3 min)
- Display results

---

## Implementation Priority

### Phase 1 (Immediate):
✅ Add seniority level to preferences  
✅ Add country selection  
✅ Add date posted filter  
✅ Update Indeed scraper to use level parameter  
✅ Update LinkedIn scraper mapping  

### Phase 2 (Soon):
⏳ Add industry/function filtering  
⏳ Add company size preference  
⏳ Improve location handling (structured)  

### Phase 3 (Later):
⏳ Salary-based filtering  
⏳ Skills-based matching  
⏳ Company-specific searches  
