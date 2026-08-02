"""Add composite database indexes for high-frequency issue feeds and notifications

Revision ID: 006
Revises: 005
Create Date: 2026-08-02
"""

from typing import Sequence, Union
from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_issues_station_public_status",
        "issues",
        ["station_id", "is_public", "status"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_issues_public_priority",
        "issues",
        ["is_public", "priority_score"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_notifications_user_read_created",
        "notifications",
        ["user_id", "is_read", "created_at"],
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("ix_notifications_user_read_created", table_name="notifications", if_exists=True)
    op.drop_index("ix_issues_public_priority", table_name="issues", if_exists=True)
    op.drop_index("ix_issues_station_public_status", table_name="issues", if_exists=True)
