"""Remove AI-era feature tables and add issue number sequence

Revision ID: 016
Revises: b01069d8a979
Create Date: 2026-11-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "016"
down_revision: Union[str, None] = "b01069d8a979"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

REMOVED_TABLES = [
    "dispatch_assignments",
    "workforce_staff",
    "station_health_snapshots",
    "vendor_penalty_notes",
    "vendor_contracts",
    "issue_feedback",
    "user_reputations",
    "emergency_alerts",
]


def upgrade() -> None:
    for table in REMOVED_TABLES:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
    op.execute("ALTER TABLE issues DROP COLUMN IF EXISTS reopen_count")
    op.execute("ALTER TABLE issues DROP COLUMN IF EXISTS resolution_photo_url")
    op.execute("ALTER TABLE issues DROP COLUMN IF EXISTS resolution_verification_score")
    op.execute("ALTER TABLE issues DROP COLUMN IF EXISTS resolution_status")

    # Race-free issue numbers; start above any number already issued.
    op.execute("CREATE SEQUENCE IF NOT EXISTS issue_number_seq")
    op.execute(
        """
        SELECT setval(
            'issue_number_seq',
            GREATEST(
                1000,
                COALESCE(
                    (SELECT MAX(CAST(split_part(issue_number, '-', 4) AS INTEGER))
                     FROM issues WHERE issue_number ~ '^RV-[A-Z]+-[0-9]{4}-[0-9]+$'),
                    0
                )
            )
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP SEQUENCE IF EXISTS issue_number_seq")
