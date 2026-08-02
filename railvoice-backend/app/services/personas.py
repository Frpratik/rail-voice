"""Product personas — Passenger, Station Admin, Main Admin."""

from __future__ import annotations

from app.core.enums import RoleCode
from app.models.user import User
from app.services.scope import official_location_scopes

# Primary product roles (keep legacy codes in DB for compatibility)
PERSONA_PASSENGER = "passenger"
PERSONA_STATION_ADMIN = "station_admin"
PERSONA_MAIN_ADMIN = "main_admin"

STATION_ADMIN_ROLE_CODES = {
    RoleCode.STATION_MODERATOR.value,
    RoleCode.STATION_MANAGER.value,
}
MAIN_ADMIN_ROLE_CODES = {
    RoleCode.SUPER_ADMIN.value,
    RoleCode.RAILWAY_ADMIN.value,
}


def user_persona(user: User) -> str:
    codes = {
        ur.role.code
        for ur in user.roles
        if ur.revoked_at is None and ur.role is not None
    }
    if codes & MAIN_ADMIN_ROLE_CODES:
        # Main admin only if unscoped (sees all stations)
        if official_location_scopes(user) is None:
            return PERSONA_MAIN_ADMIN
    if codes & STATION_ADMIN_ROLE_CODES:
        return PERSONA_STATION_ADMIN
    if codes & {RoleCode.DIVISIONAL_OFFICER.value}:
        # Treat division officers as station-admin class for product UI
        return PERSONA_STATION_ADMIN
    return PERSONA_PASSENGER


def persona_label(persona: str) -> str:
    return {
        PERSONA_PASSENGER: "Passenger",
        PERSONA_STATION_ADMIN: "Station Admin",
        PERSONA_MAIN_ADMIN: "Main Admin",
    }.get(persona, "Passenger")
