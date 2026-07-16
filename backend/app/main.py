from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api import health, auth, jobs, users, applications, profile, interview, billing, referrals, interview_coach, career, analytics, reviews, onboarding, cvs, auto_apply, career_report, salary_alerts, companies, apply_engine, webhooks, answer_bank
from app.middleware.rate_limit import RateLimitMiddleware


def _configure_logging() -> None:
    """JSON structured logging when structlog is available; else stdlib."""
    level = logging.DEBUG if settings.DEBUG else logging.INFO
    from app.core.log_redact import install_redacting_filter

    try:
        import structlog

        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(level),
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
        structlog.get_logger("jobscale").info(
            "logging_configured",
            environment=settings.ENVIRONMENT,
            json=True,
        )
    except Exception:
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
    install_redacting_filter()


def _configure_sentry() -> None:
    dsn = (getattr(settings, "SENTRY_DSN", None) or "").strip()
    if not dsn:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        sentry_sdk.init(
            dsn=dsn,
            environment=settings.ENVIRONMENT,
            traces_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 0.0,
            integrations=[FastApiIntegration(), SqlalchemyIntegration()],
        )
    except Exception as exc:
        logging.getLogger("jobscale").warning("Sentry init skipped: %s", exc)


def _configure_otel_provider() -> bool:
    """Soft-init OpenTelemetry tracer when OTEL_EXPORTER_OTLP_ENDPOINT is set."""
    endpoint = (getattr(settings, "OTEL_EXPORTER_OTLP_ENDPOINT", None) or "").strip()
    if not endpoint:
        return False
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create(
            {
                "service.name": getattr(settings, "OTEL_SERVICE_NAME", None) or "jobscale-api",
                "deployment.environment": settings.ENVIRONMENT,
            }
        )
        provider = TracerProvider(resource=resource)
        exporter_url = endpoint.rstrip("/")
        if not exporter_url.endswith("/v1/traces"):
            exporter_url = f"{exporter_url}/v1/traces"
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=exporter_url)))
        trace.set_tracer_provider(provider)
        return True
    except Exception as exc:
        logging.getLogger("jobscale").warning("OpenTelemetry init skipped: %s", exc)
        return False


_configure_logging()
_configure_sentry()
_otel_ready = _configure_otel_provider()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.assert_safe_for_production()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

if _otel_ready:
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)
    except Exception as exc:
        logging.getLogger("jobscale").warning("OpenTelemetry FastAPI instrument skipped: %s", exc)

# CORS
_cors_methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
_cors_headers = ["Authorization", "Content-Type", "Accept", "X-Requested-With"]
if str(settings.ENVIRONMENT).lower() != "production":
    _cors_methods = ["*"]
    _cors_headers = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins(),
    allow_credentials=True,
    allow_methods=_cors_methods,
    allow_headers=_cors_headers,
)
app.add_middleware(RateLimitMiddleware)

# Routes
app.include_router(health.router, prefix=f"{settings.API_V1_PREFIX}/health", tags=["Health"])
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Auth"])
app.include_router(users.router, prefix=f"{settings.API_V1_PREFIX}/users", tags=["Users"])
app.include_router(jobs.router, prefix=f"{settings.API_V1_PREFIX}/jobs", tags=["Jobs"])
app.include_router(applications.router, prefix=f"{settings.API_V1_PREFIX}/applications", tags=["Applications"])
app.include_router(profile.router, prefix=f"{settings.API_V1_PREFIX}/profile", tags=["Profile"])
app.include_router(interview.router, prefix=f"{settings.API_V1_PREFIX}/interview", tags=["Interview Prep"])
app.include_router(billing.router, prefix=f"{settings.API_V1_PREFIX}/billing", tags=["Billing"])
app.include_router(referrals.router, prefix=f"{settings.API_V1_PREFIX}/referrals", tags=["Referrals"])
app.include_router(interview_coach.router, prefix=f"{settings.API_V1_PREFIX}/interview-coach", tags=["Interview Coach"])
app.include_router(onboarding.router, prefix=f"{settings.API_V1_PREFIX}/onboarding", tags=["Onboarding"])
app.include_router(career.router, prefix=f"{settings.API_V1_PREFIX}/career", tags=["Career Pathing"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_PREFIX}/analytics", tags=["Analytics"])
app.include_router(reviews.router, prefix=f"{settings.API_V1_PREFIX}/reviews", tags=["Company Reviews"])
app.include_router(auto_apply.router, prefix=f"{settings.API_V1_PREFIX}/auto-apply", tags=["Auto-Apply"])
app.include_router(career_report.router, prefix=f"{settings.API_V1_PREFIX}/reports", tags=["Career Reports"])
app.include_router(salary_alerts.router, prefix=f"{settings.API_V1_PREFIX}/alerts", tags=["Salary Alerts"])
app.include_router(companies.router, prefix=f"{settings.API_V1_PREFIX}/companies", tags=["Companies"])
app.include_router(apply_engine.router, prefix=f"{settings.API_V1_PREFIX}/apply-engine", tags=["Apply Engine"])
app.include_router(answer_bank.router, prefix=f"{settings.API_V1_PREFIX}/answer-bank", tags=["Answer Bank"])
app.include_router(webhooks.router, prefix=f"{settings.API_V1_PREFIX}/webhooks", tags=["Webhooks"])
app.include_router(cvs.router, tags=["CVs"])


@app.get("/")
async def root():
    return {"name": settings.APP_NAME, "version": "0.1.0", "docs": "/docs"}
