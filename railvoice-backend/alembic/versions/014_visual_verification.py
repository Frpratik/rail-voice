"""Add resolution verification columns to issues table

Revision ID: a01069d8a978
Revises: 998069d8a977
Create Date: 2026-08-05 23:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a01069d8a978'
down_revision: Union[str, None] = '998069d8a977'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('issues', sa.Column('resolution_photo_url', sa.String(length=512), nullable=True))
    op.add_column('issues', sa.Column('resolution_verification_score', sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column('issues', sa.Column('resolution_status', sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column('issues', 'resolution_status')
    op.drop_column('issues', 'resolution_verification_score')
    op.drop_column('issues', 'resolution_photo_url')
