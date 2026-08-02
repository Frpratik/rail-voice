"""User management RBAC unit tests."""

from __future__ import annotations

import uuid

from app.core.enums import LocationScope, RoleCode
from app.models.user import Role, User, UserRole
from app.services.personas import PERSONA_MAIN_ADMIN
from app.services.user_management import can_manage_target


def _role_user(code: str, *, location_id=None) -> User:
    role = Role(id=uuid.uuid4(), code=code, name=code, level=10)
    user = User(id=uuid.uuid4(), display_name="U", is_active=True)
    user.roles = [
        UserRole(
            id=uuid.uuid4(),
            user_id=user.id,
            role_id=role.id,
            location_type=LocationScope.STATION.value if location_id else None,
            location_id=location_id,
            role=role,
        )
    ]
    return user


def test_main_admin_can_manage_anyone():
    admin = _role_user(RoleCode.SUPER_ADMIN.value)
    passenger = _role_user(RoleCode.PASSENGER.value)
    passenger.assigned_station_id = uuid.uuid4()
    assert can_manage_target(admin, passenger)


def test_station_admin_cannot_manage_other_station():
    station_a = uuid.uuid4()
    station_b = uuid.uuid4()
    sa = _role_user(RoleCode.STATION_MANAGER.value, location_id=station_a)
    other = _role_user(RoleCode.PASSENGER.value)
    other.assigned_station_id = station_b
    assert not can_manage_target(sa, other)


def test_station_admin_can_manage_own_station_user():
    station_a = uuid.uuid4()
    sa = _role_user(RoleCode.STATION_MANAGER.value, location_id=station_a)
    user = _role_user(RoleCode.PASSENGER.value)
    user.assigned_station_id = station_a
    assert can_manage_target(sa, user)
