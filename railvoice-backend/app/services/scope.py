"""Location-scoped query helpers for official RBAC."""

from __future__ import annotations

import uuid

from sqlalchemy import Select, or_
from sqlalchemy.orm import selectinload

from app.core.enums import LocationScope, RoleCode
from app.models.issue import Issue
from app.models.user import User, UserRole


UNSCOPED_ROLES = {RoleCode.SUPER_ADMIN.value, RoleCode.RAILWAY_ADMIN.value}


def official_location_scopes(user: User) -> dict[str, set[uuid.UUID]] | None:
    """
    Return scope buckets for the official, or None if the user is unscoped (sees all).

    None  → no location filter
    dict  → apply OR of station/division/zone filters (may be empty → no issues)
    """
    has_official = False
    unscoped = False
    scopes: dict[str, set[uuid.UUID]] = {
        LocationScope.STATION.value: set(),
        LocationScope.DIVISION.value: set(),
        LocationScope.ZONE.value: set(),
    }

    for ur in user.roles:
        if ur.revoked_at is not None or not ur.role:
            continue
        code = ur.role.code
        if code in {r.value for r in (
            RoleCode.VOLUNTEER,
            RoleCode.STATION_MODERATOR,
            RoleCode.STATION_MANAGER,
            RoleCode.DIVISIONAL_OFFICER,
            RoleCode.RAILWAY_ADMIN,
            RoleCode.SUPER_ADMIN,
        )}:
            has_official = True
        if code in UNSCOPED_ROLES and not ur.location_type:
            unscoped = True
        if ur.location_type and ur.location_id:
            bucket = scopes.get(ur.location_type)
            if bucket is not None:
                bucket.add(ur.location_id)

    if not has_official:
        return None
    if unscoped:
        return None
    # Official with no location rows → treat as unscoped (legacy seed admins)
    if not any(scopes.values()):
        return None
    return scopes


def apply_issue_location_scope(query: Select, user: User) -> Select:
    scopes = official_location_scopes(user)
    if scopes is None:
        return query

    clauses = []
    if scopes[LocationScope.STATION.value]:
        clauses.append(Issue.station_id.in_(scopes[LocationScope.STATION.value]))
    if scopes[LocationScope.DIVISION.value]:
        clauses.append(Issue.division_id.in_(scopes[LocationScope.DIVISION.value]))
    if scopes[LocationScope.ZONE.value]:
        clauses.append(Issue.zone_id.in_(scopes[LocationScope.ZONE.value]))

    if not clauses:
        # Scoped official but empty ids → see nothing
        return query.where(Issue.id == uuid.UUID("00000000-0000-0000-0000-000000000000"))
    return query.where(or_(*clauses))


def can_user_access_issue(user: User, issue: Issue) -> bool:
    scopes = official_location_scopes(user)
    if scopes is None:
        return True
    if issue.station_id and issue.station_id in scopes[LocationScope.STATION.value]:
        return True
    if issue.division_id and issue.division_id in scopes[LocationScope.DIVISION.value]:
        return True
    if issue.zone_id and issue.zone_id in scopes[LocationScope.ZONE.value]:
        return True
    return False


def enforce_issue_location_scope(user: User, issue: Issue) -> None:
    if not can_user_access_issue(user, issue):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: issue is outside your assigned station/division jurisdiction",
        )


def load_user_roles_option():
    return selectinload(User.roles).selectinload(UserRole.role)
