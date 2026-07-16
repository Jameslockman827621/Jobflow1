"""
Celery Beat Schedule Configuration

Monitoring tiers (vs previous 6h cadence):
- Hot companies: every 60 seconds (near real-time after posting)
- Warm companies: every 15 minutes
- Cold companies: every 2 hours
- Legacy Greenhouse/Lever scrapes retained as backups
"""

from celery.schedules import crontab

# Celery Beat schedule
beat_schedule = {
    # Near-real-time hot career pages
    "monitor-hot-companies": {
        "task": "app.tasks.monitoring.monitor_hot_companies",
        "schedule": 60.0,  # seconds
    },
    # Warm boards every 15 minutes
    "monitor-warm-companies": {
        "task": "app.tasks.monitoring.monitor_warm_companies",
        "schedule": crontab(minute="*/15"),
    },
    # Cold boards every 2 hours
    "monitor-cold-companies": {
        "task": "app.tasks.monitoring.monitor_cold_companies",
        "schedule": crontab(minute=10, hour="*/2"),
    },
    # Seed directory once daily (idempotent upsert)
    "seed-company-directory-daily": {
        "task": "app.tasks.monitoring.seed_company_directory",
        "schedule": crontab(minute=5, hour=2),
    },

    # Legacy Greenhouse scrape every 2 hours (backup / bootstrap)
    "scrape-greenhouse-every-2h": {
        "task": "app.tasks.jobs.scrape_greenhouse_companies",
        "schedule": crontab(minute=0, hour="*/2"),
        "args": ([
            "airbnb", "stripe", "gitlab", "figma", "monzo", "revolut",
            "coinbase", "doordash", "instacart", "robinhood", "shopify",
            "substack", "twitch", "wayfair", "zendesk", "lyft", "pinterest",
            "square", "affirm", "brex", "chime", "datadog", "dropbox",
            "fivetran", "hubspot", "intercom", "launchdarkly", "mixpanel",
            "mongodb", "okta", "pulumi", "retool", "segment", "sentry",
            "slack", "snowflake", "splunk", "twilio", "webflow", "zapier",
            "zillow", "wise", "checkout.com", "klarna", "spacex", "canva",
            "asana", "cloudflare", "plaid", "openai", "notion",
        ],),
    },

    # Lever every 2 hours
    "scrape-lever-every-2h": {
        "task": "app.tasks.jobs.scrape_lever_companies",
        "schedule": crontab(minute=30, hour="*/2"),
        "args": ([
            "netflix", "spotify", "eventbrite", "box", "yelp", "coursera",
            "duolingo", "wealthfront", "samsara", "anduril", "replit",
            "linear", "mercury", "deel", "remote", "gong",
        ],),
    },

    # Daily job cleanup - remove old/inactive jobs
    "cleanup-old-jobs-daily": {
        "task": "app.tasks.jobs.cleanup_old_jobs",
        "schedule": crontab(minute=0, hour=3),
    },

    # Recalculate match scores daily
    "recalculate-matches-daily": {
        "task": "app.tasks.jobs.recalculate_all_matches",
        "schedule": crontab(minute=0, hour=4),
    },

    # Daily job alerts
    "daily-job-alerts": {
        "task": "app.tasks.alerts.send_daily_job_alerts",
        "schedule": crontab(minute=0, hour=9),
    },

    # Weekly summary (Monday 8 AM)
    "weekly-summary": {
        "task": "app.tasks.alerts.send_weekly_summary",
        "schedule": crontab(minute=0, hour=8, day_of_week=1),
    },

    # Follow-up reminders (daily at 10 AM)
    "followup-reminders": {
        "task": "app.tasks.alerts.send_follow_up_reminders",
        "schedule": crontab(minute=0, hour=10),
    },

    # Refresh user job searches (every 2 hours — tighter freshness)
    "refresh-user-searches": {
        "task": "app.tasks.on_demand_search.refresh_all_user_searches",
        "schedule": crontab(minute=20, hour="*/2"),
    },

    # Clean expired cache (daily at 3 AM)
    "clean-expired-cache": {
        "task": "app.tasks.on_demand_search.clean_expired_cache",
        "schedule": crontab(minute=0, hour=3),
    },
}
