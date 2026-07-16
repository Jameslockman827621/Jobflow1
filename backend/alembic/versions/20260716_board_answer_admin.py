"""Add board_sessions, answer_bank; user is_admin + auto_apply_submit columns.

Revision ID: 20260716_board_answer
Revises: 20260716_monitored
Create Date: 2026-07-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "20260716_board_answer"
down_revision: Union[str, None] = "20260716_monitored"
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
    if not _has_table("board_sessions"):
        op.create_table(
            "board_sessions",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("board", sa.String(length=40), nullable=False),
            sa.Column("storage_state_json", sa.Text(), nullable=False),
            sa.Column("label", sa.String(length=120), nullable=True),
            sa.Column("expires_at", sa.DateTime(), nullable=True),
            sa.Column("last_used_at", sa.DateTime(), nullable=True),
            sa.Column("is_valid", sa.Integer(), nullable=True, server_default="1"),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_board_sessions_id", "board_sessions", ["id"])
        op.create_index("ix_board_sessions_user_id", "board_sessions", ["user_id"])
        op.create_index("idx_board_session_user", "board_sessions", ["user_id"])
        op.create_index(
            "uix_board_session_user_board",
            "board_sessions",
            ["user_id", "board"],
            unique=True,
        )

    if not _has_table("answer_bank"):
        op.create_table(
            "answer_bank",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("question_hash", sa.String(length=64), nullable=False),
            sa.Column("question", sa.Text(), nullable=False),
            sa.Column("answer", sa.Text(), nullable=False),
            sa.Column("use_count", sa.Integer(), nullable=True, server_default="1"),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_answer_bank_id", "answer_bank", ["id"])
        op.create_index("ix_answer_bank_user_id", "answer_bank", ["user_id"])
        op.create_index("ix_answer_bank_question_hash", "answer_bank", ["question_hash"])
        op.create_index("idx_answer_bank_user", "answer_bank", ["user_id"])
        op.create_index(
            "uix_answer_bank_user_q",
            "answer_bank",
            ["user_id", "question_hash"],
            unique=True,
        )

    if _has_table("users"):
        if not _has_column("users", "is_admin"):
            op.add_column(
                "users",
                sa.Column("is_admin", sa.Boolean(), nullable=True, server_default=sa.text("false")),
            )
        if not _has_column("users", "auto_apply_submit"):
            op.add_column(
                "users",
                sa.Column(
                    "auto_apply_submit",
                    sa.Boolean(),
                    nullable=True,
                    server_default=sa.text("false"),
                ),
            )


def downgrade() -> None:
    if _has_table("users"):
        if _has_column("users", "auto_apply_submit"):
            op.drop_column("users", "auto_apply_submit")
        if _has_column("users", "is_admin"):
            op.drop_column("users", "is_admin")
    if _has_table("answer_bank"):
        op.drop_table("answer_bank")
    if _has_table("board_sessions"):
        op.drop_table("board_sessions")
