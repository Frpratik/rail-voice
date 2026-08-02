"""Add user_reputations table for gamification and leaderboards

Revision ID: 009
Revises: 008
Create Date: 2026-08-02
"""

from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from alembic import op

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_reputations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tier", sa.String(20), nullable=False, server_default="bronze"),
        sa.Column("badge_slugs", ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("reports_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("verifications_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_user_reputations_points",
        "user_reputations",
        ["points"],
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("ix_user_reputations_points", table_name="user_reputations", if_exists=True)
    op.drop_table("user_reputations")
