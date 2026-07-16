"""Core schema baseline — empty DB can `alembic upgrade head` without create_all.

Revision ID: 20260716_core_baseline
Revises: None
Create Date: 2026-07-16

Idempotent: uses SQLAlchemy metadata.create_all(checkfirst=True) so existing
databases that already have tables from init_db() are safe.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20260716_core_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Import every model so Base.metadata is complete
    from app.models.base import Base
    import app.models.user  # noqa: F401
    import app.models.profile  # noqa: F401
    import app.models.job  # noqa: F401
    import app.models.application  # noqa: F401
    import app.models.preferences  # noqa: F401
    import app.models.search_cache  # noqa: F401
    import app.models.referral  # noqa: F401
    import app.models.review  # noqa: F401
    import app.models.auto_apply  # noqa: F401
    import app.models.company  # noqa: F401
    import app.models.cv  # noqa: F401
    import app.models.board_session  # noqa: F401
    import app.models.answer_bank  # noqa: F401

    bind = op.get_bind()
    Base.metadata.create_all(bind=bind, checkfirst=True)


def downgrade() -> None:
    # Do not drop core product tables — too destructive for shared DBs
    pass
