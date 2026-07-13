from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.user import Notification


def create_notification(
    session: Session,
    *,
    user_id: uuid.UUID,
    type: str,
    title: str,
    body: str,
    issue_id: uuid.UUID | None = None,
) -> Notification:
    note = Notification(
        user_id=user_id,
        type=type,
        title=title,
        body=body,
        issue_id=issue_id,
        is_read=False,
        created_at=datetime.now(timezone.utc),
    )
    session.add(note)
    session.flush()
    return note
