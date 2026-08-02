"""Add perceptual_hash column and index to issue_photos table

Revision ID: 007
Revises: 006
Create Date: 2026-08-02
"""

from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("issue_photos", sa.Column("perceptual_hash", sa.String(64), nullable=True))
    op.create_index(
        "ix_issue_photos_perceptual_hash",
        "issue_photos",
        ["perceptual_hash"],
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("ix_issue_photos_perceptual_hash", table_name="issue_photos", if_exists=True)
    op.drop_column("issue_photos", "perceptual_hash")
