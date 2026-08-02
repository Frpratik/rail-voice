"""Three-persona product model tests."""

from __future__ import annotations

import uuid

from app.core.enums import LocationScope, RoleCode
from app.models.user import Role, User, UserRole
from app.services.personas import (
    PERSONA_MAIN_ADMIN,
    PERSONA_PASSENGER,
    PERSONA_STATION_ADMIN,
    persona_label,
    user_persona,
)


def _user_with_role(code: str, *, location_type: str | None = None, location_id=None) -> User:
    role = Role(id=uuid.uuid4(), code=code, name=code, level=10)
    user = User(id=uuid.uuid4(), display_name="T", is_active=True)
    user.roles = [
        UserRole(
            id=uuid.uuid4(),
            user_id=user.id,
            role_id=role.id,
            location_type=location_type,
            location_id=location_id,
            role=role,
        )
    ]
    return user


def test_passenger_persona():
    user = _user_with_role(RoleCode.PASSENGER.value)
    assert user_persona(user) == PERSONA_PASSENGER
    assert persona_label(PERSONA_PASSENGER) == "Passenger"


def test_station_admin_persona():
    user = _user_with_role(
        RoleCode.STATION_MANAGER.value,
        location_type=LocationScope.STATION.value,
        location_id=uuid.uuid4(),
    )
    assert user_persona(user) == PERSONA_STATION_ADMIN


def test_main_admin_persona():
    user = _user_with_role(RoleCode.SUPER_ADMIN.value)
    assert user_persona(user) == PERSONA_MAIN_ADMIN
