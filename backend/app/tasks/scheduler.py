"""
Celery Beat Schedule Configuration

Automated job scraping schedules:
- Greenhouse: Every 6 hours
- Lever: Every 6 hours
- Job deduplication: Daily
- Match score recalculation: Daily
"""

from celery.schedules import crontab

# Celery Beat schedule
beat_schedule = {
    # Scrape Greenhouse companies every 6 hours
    "scrape-greenhouse-every-6h": {
        "task": "app.tasks.jobs.scrape_greenhouse_companies",
        "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
        "args": ([
            "airbnb", "stripe", "gitlab", "figma", "monzo", "revolut",
            "coinbase", "doordash", "instacart", "robinhood", "shopify",
            "substack", "twitch", "wayfair", "zendesk", "lyft", "pinterest",
            "square", "affirm", "brex", "chime", "datadog", "dropbox",
            "fivetran", "hubspot", "intercom", "launchdarkly", "mixpanel",
            "mongodb", "okta", "pulumi", "retool", "segment", "sentry",
            "slack", "snowflake", "splunk", "twilio", "webflow", "zapier",
            "zillow", "wise", "checkout.com", "klarna", "spacex", "canva",
        ],),
    },
    
    # Scrape Lever companies every 6 hours
    "scrape-lever-every-6h": {
        "task": "app.tasks.jobs.scrape_lever_companies",
        "schedule": crontab(minute=30, hour="*/6"),  # Every 6 hours, offset by 30 min
        "args": ([],),  # Empty for now - Lever needs more work
    },
    
    # Daily job cleanup - remove old/inactive jobs
    "cleanup-old-jobs-daily": {
        "task": "app.tasks.jobs.cleanup_old_jobs",
        "schedule": crontab(minute=0, hour=3),  # 3 AM daily
    },
    
    # Recalculate match scores daily
    "recalculate-matches-daily": {
        "task": "app.tasks.jobs.recalculate_all_matches",
        "schedule": crontab(minute=0, hour=4),  # 4 AM daily
    },
    
    # Daily job alerts
    "daily-job-alerts": {
        "task": "app.tasks.alerts.send_daily_job_alerts",
        "schedule": crontab(minute=0, hour=9),  # 9 AM daily
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
}
