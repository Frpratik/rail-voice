"""Add assignee fields and notifications.issue_id FK

Revision ID: 002
Revises: 001
Create Date: 2026-07-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("issues", sa.Column("assignee_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("issues", sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(
        "fk_issues_assignee_id_users",
        "issues",
        "users",
        ["assignee_id"],
        ["id"],
    )
    # Ensure notifications.issue_id references issues when missing
    try:
        op.create_foreign_key(
            "fk_notifications_issue_id_issues",
            "notifications",
            "issues",
            ["issue_id"],
            ["id"],
        )
    except Exception:
        pass


def downgrade() -> None:
    try:
        op.drop_constraint("fk_notifications_issue_id_issues", "notifications", type_="foreignkey")
    except Exception:
        pass
    op.drop_constraint("fk_issues_assignee_id_users", "issues", type_="foreignkey")
    op.drop_column("issues", "assigned_at")
    op.drop_column("issues", "assignee_id")
