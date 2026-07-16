"""Add users.google_sub; allow null hashed_password for OAuth-only accounts.

Revision ID: 20260716_google_oauth
Revises: 20260716_monitor_queue
Create Date: 2026-07-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "20260716_google_oauth"
down_revision: Union[str, None] = "20260716_monitor_queue"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    if table not in inspect(bind).get_table_names():
        return False
    return column in {c["name"] for c in inspect(bind).get_columns(table)}


def upgrade() -> None:
    if not _has_column("users", "google_sub"):
        op.add_column("users", sa.Column("google_sub", sa.String(), nullable=True))
        op.create_index("ix_users_google_sub", "users", ["google_sub"], unique=True)
    # Allow OAuth-only accounts without password
    try:
        op.alter_column("users", "hashed_password", existing_type=sa.String(), nullable=True)
    except Exception:
        pass


def downgrade() -> None:
    try:
        op.alter_column("users", "hashed_password", existing_type=sa.String(), nullable=False)
    except Exception:
        pass
    if _has_column("users", "google_sub"):
        op.drop_index("ix_users_google_sub", table_name="users")
        op.drop_column("users", "google_sub")
