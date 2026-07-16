"""Create monitored_companies and apply_runs tables; add last_fingerprint.

Revision ID: 20260716_monitored
Revises: None
Create Date: 2026-07-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "20260716_monitored"
down_revision: Union[str, None] = "20260716_core_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    return name in inspect(bind).get_table_names()


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    if table not in inspect(bind).get_table_names():
        return False
    return column in {c["name"] for c in inspect(bind).get_columns(table)}


def upgrade() -> None:
    if not _has_table("monitored_companies"):
        op.create_table(
            "monitored_companies",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("slug", sa.String(length=200), nullable=False),
            sa.Column("ats_type", sa.String(length=50), nullable=False),
            sa.Column("career_url", sa.String(length=500), nullable=True),
            sa.Column("industry", sa.String(length=100), nullable=True),
            sa.Column("country", sa.String(length=10), nullable=True, server_default="US"),
            sa.Column("priority", sa.String(length=20), nullable=True, server_default="cold"),
            sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.text("true")),
            sa.Column("last_scraped_at", sa.DateTime(), nullable=True),
            sa.Column("last_job_count", sa.Integer(), nullable=True, server_default="0"),
            sa.Column("last_fingerprint", sa.String(length=64), nullable=True),
            sa.Column("scrape_failures", sa.Integer(), nullable=True, server_default="0"),
            sa.Column("avg_scrape_ms", sa.Float(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_monitored_companies_id", "monitored_companies", ["id"])
        op.create_index("ix_monitored_companies_name", "monitored_companies", ["name"])
        op.create_index("ix_monitored_companies_slug", "monitored_companies", ["slug"])
        op.create_index("ix_monitored_companies_ats_type", "monitored_companies", ["ats_type"])
        op.create_index("ix_monitored_companies_priority", "monitored_companies", ["priority"])
        op.create_index("ix_monitored_companies_is_active", "monitored_companies", ["is_active"])
        op.create_index(
            "uix_monitored_ats_slug",
            "monitored_companies",
            ["ats_type", "slug"],
            unique=True,
        )
        op.create_index(
            "idx_monitored_priority_active",
            "monitored_companies",
            ["priority", "is_active"],
        )
    elif not _has_column("monitored_companies", "last_fingerprint"):
        op.add_column(
            "monitored_companies",
            sa.Column("last_fingerprint", sa.String(length=64), nullable=True),
        )

    if not _has_table("apply_runs"):
        op.create_table(
            "apply_runs",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("application_id", sa.Integer(), nullable=True),
            sa.Column("job_id", sa.Integer(), nullable=True),
            sa.Column("mode", sa.String(length=40), nullable=False),
            sa.Column("ats_type", sa.String(length=50), nullable=True),
            sa.Column("status", sa.String(length=40), nullable=True, server_default="queued"),
            sa.Column("steps_completed", sa.Integer(), nullable=True, server_default="0"),
            sa.Column("fields_filled", sa.Integer(), nullable=True, server_default="0"),
            sa.Column("captcha_solved", sa.Boolean(), nullable=True, server_default=sa.text("false")),
            sa.Column("error", sa.Text(), nullable=True),
            sa.Column("started_at", sa.DateTime(), nullable=True),
            sa.Column("finished_at", sa.DateTime(), nullable=True),
            sa.Column("meta_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_apply_runs_id", "apply_runs", ["id"])
        op.create_index("ix_apply_runs_user_id", "apply_runs", ["user_id"])
        op.create_index("ix_apply_runs_application_id", "apply_runs", ["application_id"])
        op.create_index("ix_apply_runs_job_id", "apply_runs", ["job_id"])


def downgrade() -> None:
    if _has_table("apply_runs"):
        op.drop_table("apply_runs")
    if _has_table("monitored_companies"):
        if _has_column("monitored_companies", "last_fingerprint") and _has_table("monitored_companies"):
            # Drop whole table on downgrade of this bootstrap revision
            op.drop_table("monitored_companies")
