"""pnr and train telemetry fields

Revision ID: 011
Revises: 010
Create Date: 2026-08-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '011'
down_revision: Union[str, None] = '010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('issues', sa.Column('pnr_number', sa.String(length=10), nullable=True))
    op.add_column('issues', sa.Column('berth_number', sa.String(length=10), nullable=True))
    op.add_column('issues', sa.Column('upcoming_station_code', sa.String(length=10), nullable=True))


def downgrade() -> None:
    op.drop_column('issues', 'upcoming_station_code')
    op.drop_column('issues', 'berth_number')
    op.drop_column('issues', 'pnr_number')
