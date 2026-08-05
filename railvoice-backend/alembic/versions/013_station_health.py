"""Add station health snapshots table

Revision ID: 998069d8a977
Revises: 887069d8a976
Create Date: 2026-08-05 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '998069d8a977'
down_revision: Union[str, None] = '887069d8a976'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('station_health_snapshots',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('station_id', sa.UUID(), nullable=False),
        sa.Column('health_score', sa.Float(), nullable=False),
        sa.Column('active_issues_count', sa.Integer(), nullable=False),
        sa.Column('critical_issues_count', sa.Integer(), nullable=False),
        sa.Column('snapshot_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['station_id'], ['stations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('station_health_snapshots')
