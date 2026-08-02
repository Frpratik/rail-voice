"""Enterprise user management service — RBAC, audits, soft delete."""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import RoleCode
from app.core.security import generate_temporary_password, hash_password, hash_value, verify_password
from app.models.issue import Comment, Issue, IssueSupport
from app.models.location import Station
from app.models.user import RefreshToken, Role, User, UserManagementAudit, UserRole
from app.services.personas import (
    MAIN_ADMIN_ROLE_CODES,
    PERSONA_MAIN_ADMIN,
    PERSONA_STATION_ADMIN,
    STATION_ADMIN_ROLE_CODES,
    user_persona,
)
from app.services.scope import official_location_scopes

MOBILE_RE = re.compile(r"^\+91\d{10}$")


MANAGEABLE_ROLES = {
    RoleCode.PASSENGER.value,
    RoleCode.STATION_MANAGER.value,
    RoleCode.SUPER_ADMIN.value,
}


def actor_station_ids(actor: User) -> set[uuid.UUID] | None:
    """None = all stations (Main Admin). Set = Station Admin scope."""
    persona = user_persona(actor)
    if persona == PERSONA_MAIN_ADMIN:
        return None
    scopes = official_location_scopes(actor)
    if not scopes:
        return set()
    return set(scopes.get("station") or set())


def can_manage_target(actor: User, target: User) -> bool:
    if actor.id == target.id and user_persona(actor) != PERSONA_MAIN_ADMIN:
        # Station admins may edit themselves for basic fields via /me, not full admin mutate
        return False
    station_ids = actor_station_ids(actor)
    target_persona = user_persona(target)

    if station_ids is None:
        return True  # Main Admin

    # Station Admin: never touch Main Admins or other station users
    if target_persona == PERSONA_MAIN_ADMIN:
        return False
    if target.assigned_station_id and target.assigned_station_id in station_ids:
        return True
    # Also include station staff whose role is scoped to actor stations
    for ur in target.roles:
        if ur.revoked_at is not None or not ur.role:
            continue
        if ur.location_type == "station" and ur.location_id in station_ids:
            return True
    return False


async def write_user_audit(
    db: AsyncSession,
    *,
    action: str,
    actor: User | None,
    target: User,
    previous: dict[str, Any] | None = None,
    new: dict[str, Any] | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
) -> None:
    db.add(
        UserManagementAudit(
            action=action,
            actor_user_id=actor.id if actor else None,
            actor_name=actor.display_name if actor else None,
            target_user_id=target.id,
            target_user_name=target.display_name,
            previous_value=previous,
            new_value=new,
            ip=ip,
            user_agent=(user_agent or "")[:512] or None,
        )
    )


async def revoke_user_sessions(db: AsyncSession, user_id: uuid.UUID) -> None:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
    )
    for token in result.scalars().all():
        token.revoked_at = now


def _status_label(user: User) -> str:
    if user.deleted_at:
        return "deleted"
    if user.is_locked:
        return "locked"
    if not user.is_active:
        return "inactive"
    return "active"


USER_LOAD_OPTIONS = (
    selectinload(User.roles).selectinload(UserRole.role),
    selectinload(User.assigned_station),
)


async def load_user(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await db.execute(
        select(User).options(*USER_LOAD_OPTIONS).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def serialize_user_admin(db: AsyncSession, user: User) -> dict[str, Any]:
    from app.services.personas import persona_label

    # Always re-load with explicit options — never trigger lazy IO in async.
    loaded = await load_user(db, user.id)
    if loaded is None:
        raise LookupError("User not found")
    user = loaded

    roles = [ur.role.code for ur in user.roles if ur.revoked_at is None and ur.role]
    persona = user_persona(user)
    station = None
    if user.assigned_station is not None:
        st = user.assigned_station
        station = {"id": str(st.id), "code": st.code, "name": st.name}
    elif user.assigned_station_id:
        st = await db.get(Station, user.assigned_station_id)
        if st:
            station = {"id": str(st.id), "code": st.code, "name": st.name}

    issues_created = await db.scalar(
        select(func.count()).select_from(Issue).where(Issue.creator_id == user.id)
    )
    supports = await db.scalar(
        select(func.count()).select_from(IssueSupport).where(IssueSupport.user_id == user.id)
    )
    comments = await db.scalar(
        select(func.count()).select_from(Comment).where(Comment.user_id == user.id)
    )

    return {
        "id": str(user.id),
        "display_name": user.display_name,
        "email": user.email,
        "mobile_last4": user.mobile_last4,
        "avatar_url": user.avatar_url,
        "preferred_language": user.preferred_language,
        "is_verified": user.is_verified,
        "is_anonymous": user.is_anonymous,
        "is_active": user.is_active,
        "is_locked": user.is_locked,
        "locked_at": user.locked_at.isoformat() if user.locked_at else None,
        "locked_reason": user.locked_reason,
        "must_change_password": user.must_change_password,
        "has_password": bool(user.password_hash),
        "status": _status_label(user),
        "roles": roles,
        "persona": persona,
        "persona_label": persona_label(persona),
        "assigned_station": station,
        "assigned_station_id": str(user.assigned_station_id) if user.assigned_station_id else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "deleted_at": user.deleted_at.isoformat() if user.deleted_at else None,
        "activity_summary": {
            "issues_created": issues_created or 0,
            "supports": supports or 0,
            "comments": comments or 0,
        },
    }


async def list_users(
    db: AsyncSession,
    actor: User,
    *,
    q: str | None = None,
    status_filter: str | None = None,
    role: str | None = None,
    station_id: uuid.UUID | None = None,
    sort: str = "created_at",
    order: str = "desc",
    page: int = 1,
    page_size: int = 20,
    include_deleted: bool = False,
) -> dict[str, Any]:
    station_ids = actor_station_ids(actor)
    query = select(User).options(*USER_LOAD_OPTIONS).where(User.is_anonymous.is_(False))

    if include_deleted and station_ids is None:
        pass  # Main Admin may include deleted
    else:
        query = query.where(User.deleted_at.is_(None))

    if station_ids is not None:
        # Restrict to assigned station OR role scoped to station
        if not station_ids:
            query = query.where(User.id == uuid.UUID("00000000-0000-0000-0000-000000000000"))
        else:
            scoped_role_user_ids = select(UserRole.user_id).where(
                UserRole.revoked_at.is_(None),
                UserRole.location_type == "station",
                UserRole.location_id.in_(station_ids),
            )
            query = query.where(
                or_(
                    User.assigned_station_id.in_(station_ids),
                    User.id.in_(scoped_role_user_ids),
                )
            )
            # Hide Main Admins from station admin lists
            main_role_ids = select(Role.id).where(Role.code.in_(list(MAIN_ADMIN_ROLE_CODES)))
            main_user_ids = select(UserRole.user_id).where(
                UserRole.role_id.in_(main_role_ids),
                UserRole.revoked_at.is_(None),
            )
            query = query.where(User.id.notin_(main_user_ids))

    if q:
        like = f"%{q.strip()}%"
        query = query.where(
            or_(
                User.display_name.ilike(like),
                User.email.ilike(like),
                User.mobile_last4.ilike(like),
            )
        )

    if status_filter == "active":
        query = query.where(User.is_active.is_(True), User.is_locked.is_(False), User.deleted_at.is_(None))
    elif status_filter == "inactive":
        query = query.where(User.is_active.is_(False), User.deleted_at.is_(None))
    elif status_filter == "locked":
        query = query.where(User.is_locked.is_(True), User.deleted_at.is_(None))
    elif status_filter == "deleted":
        query = query.where(User.deleted_at.is_not(None))

    if role:
        role_row = (await db.execute(select(Role).where(Role.code == role))).scalar_one_or_none()
        if role_row:
            role_users = select(UserRole.user_id).where(
                UserRole.role_id == role_row.id,
                UserRole.revoked_at.is_(None),
            )
            query = query.where(User.id.in_(role_users))

    if station_id:
        if station_ids is not None and station_id not in station_ids:
            raise PermissionError("Cannot filter outside your station")
        query = query.where(User.assigned_station_id == station_id)

    sort_map = {
        "created_at": User.created_at,
        "display_name": User.display_name,
        "last_login_at": User.last_login_at,
        "updated_at": User.updated_at,
    }
    sort_col = sort_map.get(sort, User.created_at)
    query = query.order_by(sort_col.desc() if order.lower() == "desc" else sort_col.asc())

    count_q = select(func.count()).select_from(query.order_by(None).subquery())
    total = await db.scalar(count_q) or 0

    page = max(1, page)
    page_size = min(100, max(1, page_size))
    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    users = result.scalars().unique().all()

    items = [await serialize_user_admin(db, u) for u in users]
    return {
        "items": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_count": total,
            "total_pages": (total + page_size - 1) // page_size if page_size else 0,
        },
    }


async def get_user_for_admin(db: AsyncSession, actor: User, user_id: uuid.UUID) -> User:
    user = await load_user(db, user_id)
    if not user or user.is_anonymous:
        raise LookupError("User not found")
    if user_persona(actor) == PERSONA_MAIN_ADMIN:
        return user
    if not can_manage_target(actor, user):
        raise PermissionError("Not allowed to access this user")
    return user


async def create_user(
    db: AsyncSession,
    actor: User,
    *,
    mobile: str,
    display_name: str,
    email: str | None = None,
    role_code: str = RoleCode.PASSENGER.value,
    station_id: uuid.UUID | None = None,
    generate_password: bool = True,
    ip: str | None = None,
    user_agent: str | None = None,
) -> tuple[User, str | None]:
    """Main Admin only — provision a registered user (OTP login still works for that mobile)."""
    if user_persona(actor) != PERSONA_MAIN_ADMIN:
        raise PermissionError("Only Main Admin can create users")
    mobile = mobile.strip()
    if not MOBILE_RE.match(mobile):
        raise ValueError("Mobile must be +91 followed by 10 digits")
    if role_code not in MANAGEABLE_ROLES:
        raise ValueError(f"Unsupported role: {role_code}")
    if role_code == RoleCode.STATION_MANAGER.value and not station_id:
        raise ValueError("station_id required for Station Admin role")

    mobile_hash = hash_value(mobile)
    existing = (
        await db.execute(select(User).where(User.mobile_hash == mobile_hash))
    ).scalar_one_or_none()
    if existing and existing.deleted_at is None:
        raise ValueError("A user with this mobile already exists")
    if existing and existing.deleted_at is not None:
        raise ValueError("A deleted user exists with this mobile — restore instead")

    if email:
        email = email.strip().lower()
        email_hit = (
            await db.execute(
                select(User).where(User.email == email, User.deleted_at.is_(None))
            )
        ).scalar_one_or_none()
        if email_hit:
            raise ValueError("A user with this email already exists")

    role = (await db.execute(select(Role).where(Role.code == role_code))).scalar_one_or_none()
    if not role:
        raise ValueError("Role not found")

    location_type = None
    location_id = None
    assigned_station_id = None
    if role_code == RoleCode.STATION_MANAGER.value:
        st = await db.get(Station, station_id)
        if not st:
            raise ValueError("Station not found")
        location_type = "station"
        location_id = station_id
        assigned_station_id = station_id
    elif station_id:
        st = await db.get(Station, station_id)
        if not st:
            raise ValueError("Station not found")
        assigned_station_id = station_id

    temp: str | None = None
    password_hash = None
    must_change = False
    if generate_password:
        temp = generate_temporary_password()
        password_hash = hash_password(temp)
        must_change = True

    user = User(
        display_name=display_name.strip()[:100],
        mobile_hash=mobile_hash,
        mobile_last4=mobile[-4:],
        email=email,
        is_verified=True,
        is_active=True,
        is_anonymous=False,
        assigned_station_id=assigned_station_id,
        password_hash=password_hash,
        must_change_password=must_change,
    )
    db.add(user)
    await db.flush()

    db.add(
        UserRole(
            user_id=user.id,
            role_id=role.id,
            location_type=location_type,
            location_id=location_id,
        )
    )
    await write_user_audit(
        db,
        action="user.created",
        actor=actor,
        target=user,
        previous=None,
        new={
            "display_name": user.display_name,
            "mobile_last4": user.mobile_last4,
            "email": user.email,
            "roles": [role_code],
            "station_id": str(assigned_station_id) if assigned_station_id else None,
            "has_password": bool(password_hash),
        },
        ip=ip,
        user_agent=user_agent,
    )
    await db.flush()
    loaded = await load_user(db, user.id)
    assert loaded is not None
    return loaded, temp


async def update_user_profile_fields(
    db: AsyncSession,
    actor: User,
    target: User,
    *,
    display_name: str | None = None,
    email: str | None = None,
    preferred_language: str | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
) -> User:
    is_self = actor.id == target.id
    if not is_self and not can_manage_target(actor, target):
        raise PermissionError("Not allowed")

    previous = {
        "display_name": target.display_name,
        "email": target.email,
        "preferred_language": target.preferred_language,
    }
    if display_name is not None:
        target.display_name = display_name.strip()[:100]
    if email is not None:
        target.email = email.strip().lower() or None
    if preferred_language is not None:
        target.preferred_language = preferred_language[:5]

    await write_user_audit(
        db,
        action="user.updated",
        actor=actor,
        target=target,
        previous=previous,
        new={
            "display_name": target.display_name,
            "email": target.email,
            "preferred_language": target.preferred_language,
        },
        ip=ip,
        user_agent=user_agent,
    )
    await db.flush()
    return target


async def set_active(
    db: AsyncSession,
    actor: User,
    target: User,
    *,
    active: bool,
    ip: str | None = None,
    user_agent: str | None = None,
) -> User:
    if not can_manage_target(actor, target):
        raise PermissionError("Not allowed")
    if target.id == actor.id:
        raise PermissionError("Cannot change your own active status")
    previous = {"is_active": target.is_active}
    target.is_active = active
    if not active:
        await revoke_user_sessions(db, target.id)
    await write_user_audit(
        db,
        action="account.activated" if active else "account.deactivated",
        actor=actor,
        target=target,
        previous=previous,
        new={"is_active": active},
        ip=ip,
        user_agent=user_agent,
    )
    await db.flush()
    return target


async def set_locked(
    db: AsyncSession,
    actor: User,
    target: User,
    *,
    locked: bool,
    reason: str | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
) -> User:
    if not can_manage_target(actor, target):
        raise PermissionError("Not allowed")
    if target.id == actor.id:
        raise PermissionError("Cannot lock/unlock yourself")
    previous = {"is_locked": target.is_locked, "locked_reason": target.locked_reason}
    target.is_locked = locked
    if locked:
        target.locked_at = datetime.now(timezone.utc)
        target.locked_reason = (reason or "Locked by administrator")[:255]
        await revoke_user_sessions(db, target.id)
    else:
        target.locked_at = None
        target.locked_reason = None
    await write_user_audit(
        db,
        action="account.locked" if locked else "account.unlocked",
        actor=actor,
        target=target,
        previous=previous,
        new={"is_locked": locked, "locked_reason": target.locked_reason},
        ip=ip,
        user_agent=user_agent,
    )
    await db.flush()
    return target


async def soft_delete_user(
    db: AsyncSession,
    actor: User,
    target: User,
    *,
    ip: str | None = None,
    user_agent: str | None = None,
) -> User:
    if user_persona(actor) != PERSONA_MAIN_ADMIN:
        raise PermissionError("Only Main Admin can delete users")
    if target.id == actor.id:
        raise PermissionError("Cannot delete yourself")
    previous = {"deleted_at": None}
    target.deleted_at = datetime.now(timezone.utc)
    target.is_active = False
    await revoke_user_sessions(db, target.id)
    await write_user_audit(
        db,
        action="user.deleted",
        actor=actor,
        target=target,
        previous=previous,
        new={"deleted_at": target.deleted_at.isoformat()},
        ip=ip,
        user_agent=user_agent,
    )
    await db.flush()
    return target


async def restore_user(
    db: AsyncSession,
    actor: User,
    target: User,
    *,
    ip: str | None = None,
    user_agent: str | None = None,
) -> User:
    if user_persona(actor) != PERSONA_MAIN_ADMIN:
        raise PermissionError("Only Main Admin can restore users")
    previous = {"deleted_at": target.deleted_at.isoformat() if target.deleted_at else None}
    target.deleted_at = None
    target.is_active = True
    await write_user_audit(
        db,
        action="user.restored",
        actor=actor,
        target=target,
        previous=previous,
        new={"deleted_at": None, "is_active": True},
        ip=ip,
        user_agent=user_agent,
    )
    await db.flush()
    return target


async def reset_password(
    db: AsyncSession,
    actor: User,
    target: User,
    *,
    ip: str | None = None,
    user_agent: str | None = None,
) -> str:
    if not can_manage_target(actor, target):
        raise PermissionError("Not allowed")
    temp = generate_temporary_password()
    target.password_hash = hash_password(temp)
    target.must_change_password = True
    await revoke_user_sessions(db, target.id)
    await write_user_audit(
        db,
        action="password.reset",
        actor=actor,
        target=target,
        previous={"has_password": True},
        new={"must_change_password": True},
        ip=ip,
        user_agent=user_agent,
    )
    await db.flush()
    return temp


async def assign_role(
    db: AsyncSession,
    actor: User,
    target: User,
    *,
    role_code: str,
    station_id: uuid.UUID | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
) -> User:
    if user_persona(actor) != PERSONA_MAIN_ADMIN:
        raise PermissionError("Only Main Admin can change roles")
    if role_code not in MANAGEABLE_ROLES:
        raise ValueError(f"Unsupported role: {role_code}")
    if role_code == RoleCode.SUPER_ADMIN.value and target.id == actor.id:
        pass  # ok
    if role_code == RoleCode.STATION_MANAGER.value and not station_id:
        raise ValueError("station_id required for Station Admin role")

    role = (await db.execute(select(Role).where(Role.code == role_code))).scalar_one_or_none()
    if not role:
        raise ValueError("Role not found")

    previous_roles = [ur.role.code for ur in target.roles if ur.revoked_at is None and ur.role]
    now = datetime.now(timezone.utc)
    for ur in target.roles:
        if ur.revoked_at is None:
            ur.revoked_at = now

    location_type = None
    location_id = None
    if role_code == RoleCode.STATION_MANAGER.value:
        location_type = "station"
        location_id = station_id
        target.assigned_station_id = station_id
    elif role_code == RoleCode.PASSENGER.value:
        # keep assigned_station if set
        pass
    elif role_code == RoleCode.SUPER_ADMIN.value:
        target.assigned_station_id = None

    db.add(
        UserRole(
            user_id=target.id,
            role_id=role.id,
            location_type=location_type,
            location_id=location_id,
        )
    )
    await write_user_audit(
        db,
        action="role.changed",
        actor=actor,
        target=target,
        previous={"roles": previous_roles},
        new={"roles": [role_code], "station_id": str(station_id) if station_id else None},
        ip=ip,
        user_agent=user_agent,
    )
    await db.flush()
    loaded = await load_user(db, target.id)
    assert loaded is not None
    return loaded


async def assign_station(
    db: AsyncSession,
    actor: User,
    target: User,
    *,
    station_id: uuid.UUID | None,
    ip: str | None = None,
    user_agent: str | None = None,
) -> User:
    if user_persona(actor) != PERSONA_MAIN_ADMIN:
        raise PermissionError("Only Main Admin can assign stations")
    previous = {"assigned_station_id": str(target.assigned_station_id) if target.assigned_station_id else None}
    if station_id:
        st = await db.get(Station, station_id)
        if not st:
            raise ValueError("Station not found")
    target.assigned_station_id = station_id

    # If target is station admin, update role location too
    for ur in target.roles:
        if ur.revoked_at is None and ur.role and ur.role.code in STATION_ADMIN_ROLE_CODES:
            ur.location_type = "station" if station_id else None
            ur.location_id = station_id

    await write_user_audit(
        db,
        action="station.changed",
        actor=actor,
        target=target,
        previous=previous,
        new={"assigned_station_id": str(station_id) if station_id else None},
        ip=ip,
        user_agent=user_agent,
    )
    await db.flush()
    loaded = await load_user(db, target.id)
    assert loaded is not None
    return loaded


async def change_own_password(
    db: AsyncSession,
    user: User,
    *,
    current_password: str | None,
    new_password: str,
) -> None:
    if len(new_password) < 8:
        raise ValueError("Password must be at least 8 characters")
    if user.password_hash:
        if not current_password or not verify_password(current_password, user.password_hash):
            raise PermissionError("Current password is incorrect")
    user.password_hash = hash_password(new_password)
    user.must_change_password = False
    await write_user_audit(
        db,
        action="password.changed",
        actor=user,
        target=user,
        previous={},
        new={"must_change_password": False},
    )
    await db.flush()


async def list_audits_for_user(
    db: AsyncSession,
    actor: User,
    target_id: uuid.UUID,
    *,
    limit: int = 50,
) -> list[dict[str, Any]]:
    target = await get_user_for_admin(db, actor, target_id)
    if user_persona(actor) == PERSONA_STATION_ADMIN and not can_manage_target(actor, target):
        raise PermissionError("Not allowed")
    result = await db.execute(
        select(UserManagementAudit)
        .where(UserManagementAudit.target_user_id == target_id)
        .order_by(UserManagementAudit.created_at.desc())
        .limit(limit)
    )
    rows = []
    for row in result.scalars().all():
        rows.append(
            {
                "id": str(row.id),
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "action": row.action,
                "actor_name": row.actor_name,
                "target_user_name": row.target_user_name,
                "previous_value": row.previous_value,
                "new_value": row.new_value,
            }
        )
    return rows
