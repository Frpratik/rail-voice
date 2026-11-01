"""Hide already-withdrawn issues from public lists

Revision ID: 018
Revises: 017
Create Date: 2026-11-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "018"
down_revision: Union[str, None] = "017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE issues SET is_public = false WHERE status = 'withdrawn'")


def downgrade() -> None:
    pass
