"""Add HNSW vector index on issues embedding column

Revision ID: 005
Revises: 004
Create Date: 2026-08-02
"""

from typing import Sequence, Union
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
