from collections.abc import AsyncGenerator
from typing import Annotated
import uuid

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import OFFICIAL_ROLES, RoleCode
from app.core.security import verify_access_token
from app.db.session import get_db
from app.models.user import User, UserRole

security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    db: Annotated[AsyncSession, Depends(get_db)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)] = None,
    x_anonymous_session: Annotated[str | None, Header()] = None,
) -> User | None:
    if credentials and credentials.credentials:
        payload = verify_access_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        result = await db.execute(
            select(User)
            .options(selectinload(User.roles).selectinload(UserRole.role))
            .where(User.id == uuid.UUID(user_id), User.deleted_at.is_(None))
        )
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
        if getattr(user, "is_locked", False):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is locked")
        return user

    if x_anonymous_session:
        try:
            session_id = uuid.UUID(x_anonymous_session)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid anonymous session") from exc
        result = await db.execute(
            select(User).where(User.anonymous_session_id == session_id, User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()
    return None


async def get_current_user(
    user: Annotated[User | None, Depends(get_current_user_optional)],
) -> User:
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user


async def get_reporter_user(
    user: Annotated[User | None, Depends(get_current_user_optional)],
) -> User:
    """Require a signed-in, non-anonymous passenger identity."""
    if not user or user.is_anonymous:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sign in to continue",
        )
    return user


def user_has_role(user: User, role_code: RoleCode) -> bool:
    return any(ur.role.code == role_code.value and ur.revoked_at is None for ur in user.roles)


def user_is_official(user: User) -> bool:
    return any(
        ur.role.code in {r.value for r in OFFICIAL_ROLES} and ur.revoked_at is None for ur in user.roles
    )


async def require_official(user: Annotated[User, Depends(get_current_user)]) -> User:
    if not user_is_official(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Official access required")
    return user


async def require_user_manager(user: Annotated[User, Depends(get_current_user)]) -> User:
    """Master Admin or Station Admin may manage users (scoped in service)."""
    from app.services.personas import PERSONA_MAIN_ADMIN, PERSONA_STATION_ADMIN, user_persona

    if user_persona(user) not in {PERSONA_MAIN_ADMIN, PERSONA_STATION_ADMIN}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User management access required")
    return user


async def require_main_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    from app.services.personas import PERSONA_MAIN_ADMIN, user_persona

    if user_persona(user) != PERSONA_MAIN_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Main Admin access required")
    return user
