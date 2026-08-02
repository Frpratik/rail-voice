from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory
from app.models.user import AuthAuditEvent

logger = logging.getLogger(__name__)


async def write_auth_audit(
    db: AsyncSession,
    *,
    event_type: str,
    success: bool,
    actor_user_id: uuid.UUID | None = None,
    mobile_hash: str | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
    detail: dict[str, Any] | None = None,
) -> None:
    db.add(
        AuthAuditEvent(
            event_type=event_type,
            success=success,
            actor_user_id=actor_user_id,
            mobile_hash=mobile_hash,
            ip=ip,
            user_agent=(user_agent or "")[:512] or None,
            detail=detail or {},
        )
    )
    logger.info(
        "auth_audit event=%s success=%s user=%s ip=%s",
        event_type,
        success,
        actor_user_id,
        ip,
    )


async def write_auth_audit_committed(
    *,
    event_type: str,
    success: bool,
    actor_user_id: uuid.UUID | None = None,
    mobile_hash: str | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
    detail: dict[str, Any] | None = None,
) -> None:
    """Persist audit outside the request transaction (survives HTTPException rollback)."""
    try:
        async with async_session_factory() as session:
            async with session.begin():
                await write_auth_audit(
                    session,
                    event_type=event_type,
                    success=success,
                    actor_user_id=actor_user_id,
                    mobile_hash=mobile_hash,
                    ip=ip,
                    user_agent=user_agent,
                    detail=detail,
                )
    except Exception:
        logger.exception("Failed to persist auth audit event=%s", event_type)
