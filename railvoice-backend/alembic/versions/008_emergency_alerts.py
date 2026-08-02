"""Add emergency_alerts table for station safety broadcasts

Revision ID: 008
Revises: 007
Create Date: 2026-08-02
"""

from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from alembic import op

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "emergency_alerts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("station_id", UUID(as_uuid=True), sa.ForeignKey("stations.id"), nullable=True),
        sa.Column("issuer_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False, server_default="warning"),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_emergency_alerts_station_active",
        "emergency_alerts",
        ["station_id", "is_active"],
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("ix_emergency_alerts_station_active", table_name="emergency_alerts", if_exists=True)
    op.drop_table("emergency_alerts")
