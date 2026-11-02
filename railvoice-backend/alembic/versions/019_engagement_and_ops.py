"""Follows, favourites, ratings, departments and resolution photos

Revision ID: 019
Revises: 018
Create Date: 2026-11-02 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "019"
down_revision: Union[str, None] = "018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    uuid_type = postgresql.UUID(as_uuid=True)
    op.create_table(
        "issue_followers",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("issue_id", uuid_type, sa.ForeignKey("issues.id"), nullable=False),
        sa.Column("user_id", uuid_type, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("issue_id", "user_id"),
    )
    op.create_index("ix_issue_followers_user", "issue_followers", ["user_id"])

    op.create_table(
        "station_favourites",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("station_id", uuid_type, sa.ForeignKey("stations.id"), nullable=False),
        sa.Column("user_id", uuid_type, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("station_id", "user_id"),
    )

    op.create_table(
        "issue_ratings",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("issue_id", uuid_type, sa.ForeignKey("issues.id"), nullable=False),
        sa.Column("user_id", uuid_type, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("issue_id", "user_id"),
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_issue_ratings_range"),
    )

    op.add_column("issues", sa.Column("department", sa.String(length=30), nullable=True))
    op.add_column(
        "issues",
        sa.Column("auto_escalated", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column(
        "issue_photos",
        sa.Column("kind", sa.String(length=20), server_default="evidence", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("issue_photos", "kind")
    op.drop_column("issues", "auto_escalated")
    op.drop_column("issues", "department")
    op.drop_table("issue_ratings")
    op.drop_table("station_favourites")
    op.drop_table("issue_followers")
