"""User management schema extensions (lock, password, station assignment, audits)

Revision ID: 004
Revises: 003
Create Date: 2026-07-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("is_locked", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    op.add_column("users", sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("locked_reason", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("password_hash", sa.String(length=255), nullable=True))
    op.add_column(
        "users",
        sa.Column("must_change_password", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column("users", sa.Column("mobile_last4", sa.String(length=4), nullable=True))
    op.add_column("users", sa.Column("assigned_station_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_users_assigned_station_id_stations",
        "users",
        "stations",
        ["assigned_station_id"],
        ["id"],
    )

    op.create_table(
        "user_management_audits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("actor_name", sa.String(length=100), nullable=True),
        sa.Column("target_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("target_user_name", sa.String(length=100), nullable=True),
        sa.Column("previous_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("new_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
    )
    op.create_index("ix_user_management_audits_created_at", "user_management_audits", ["created_at"])
    op.create_index("ix_user_management_audits_action", "user_management_audits", ["action"])
    op.create_index("ix_user_management_audits_target_user_id", "user_management_audits", ["target_user_id"])


def downgrade() -> None:
    op.drop_index("ix_user_management_audits_target_user_id", table_name="user_management_audits")
    op.drop_index("ix_user_management_audits_action", table_name="user_management_audits")
    op.drop_index("ix_user_management_audits_created_at", table_name="user_management_audits")
    op.drop_table("user_management_audits")
    op.drop_constraint("fk_users_assigned_station_id_stations", "users", type_="foreignkey")
    op.drop_column("users", "assigned_station_id")
    op.drop_column("users", "mobile_last4")
    op.drop_column("users", "must_change_password")
    op.drop_column("users", "password_hash")
    op.drop_column("users", "locked_reason")
    op.drop_column("users", "locked_at")
    op.drop_column("users", "is_locked")
