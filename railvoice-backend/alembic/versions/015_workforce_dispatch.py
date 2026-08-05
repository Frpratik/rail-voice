"""Add workforce staff and dispatch assignments tables

Revision ID: b01069d8a979
Revises: a01069d8a978
Create Date: 2026-08-06 00:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = 'b01069d8a979'
down_revision: Union[str, None] = 'a01069d8a978'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'workforce_staff',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('full_name', sa.String(length=150), nullable=False),
        sa.Column('skill_category', sa.String(length=50), nullable=False), # housekeeping, electrical, mechanical, safety
        sa.Column('contact_number', sa.String(length=20), nullable=True),
        sa.Column('assigned_station_id', UUID(as_uuid=True), sa.ForeignKey('stations.id'), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='available'), # available, on_task, off_duty
        sa.Column('shift_start', sa.String(length=10), nullable=True),
        sa.Column('shift_end', sa.String(length=10), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    op.create_table(
        'dispatch_assignments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('issue_id', UUID(as_uuid=True), sa.ForeignKey('issues.id'), nullable=False),
        sa.Column('staff_id', UUID(as_uuid=True), sa.ForeignKey('workforce_staff.id'), nullable=False),
        sa.Column('dispatch_status', sa.String(length=30), nullable=False, server_default='dispatched'), # dispatched, accepted, in_progress, completed
        sa.Column('matched_skill', sa.String(length=50), nullable=True),
        sa.Column('confidence_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('dispatched_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('dispatch_assignments')
    op.drop_table('workforce_staff')
