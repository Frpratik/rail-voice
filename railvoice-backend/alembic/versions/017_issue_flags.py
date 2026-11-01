"""Add issue_flags for passenger reports of spam/abuse

Revision ID: 017
Revises: 016
Create Date: 2026-11-02 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "017"
down_revision: Union[str, None] = "016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "issue_flags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("issue_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("issues.id"), nullable=False),
        sa.Column("comment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("comments.id"), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reason", sa.String(30), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("resolution", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("user_id", "issue_id", "comment_id"),
    )
    op.create_index("ix_issue_flags_open", "issue_flags", ["resolved_at", "created_at"])
    op.create_index("ix_issue_flags_issue", "issue_flags", ["issue_id"])


def downgrade() -> None:
    op.drop_table("issue_flags")
