"""Add users.monitor_auto_queue for career-page auto-queue opt-in.

Revision ID: 20260716_monitor_queue
Revises: 20260716_board_answer
Create Date: 2026-07-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "20260716_monitor_queue"
down_revision: Union[str, None] = "20260716_board_answer"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    if table not in inspect(bind).get_table_names():
        return False
    return column in {c["name"] for c in inspect(bind).get_columns(table)}


def upgrade() -> None:
    if not _has_column("users", "monitor_auto_queue"):
        op.add_column(
            "users",
            sa.Column(
                "monitor_auto_queue",
                sa.Boolean(),
                nullable=True,
                server_default=sa.text("false"),
            ),
        )


def downgrade() -> None:
    if _has_column("users", "monitor_auto_queue"):
        op.drop_column("users", "monitor_auto_queue")
