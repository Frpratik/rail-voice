"""Seed Western Railway corridor data."""

from __future__ import annotations

import uuid

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_value
from app.models.issue import SystemConfig
from app.models.location import Division, IssueCategory, Station, Zone
from app.models.user import Role, User, UserRole

STATIONS = [
    (1, "CCG", "Churchgate", 18.9322, 72.8265),
    (2, "MEL", "Marine Lines", 18.9456, 72.8235),
    (3, "CYR", "Charni Road", 18.9517, 72.8194),
    (4, "GRD", "Grant Road", 18.9602, 72.8162),
    (5, "BCT", "Mumbai Central", 18.9698, 72.8190),
    (6, "MX", "Mahalaxmi", 18.9827, 72.8197),
    (7, "PL", "Lower Parel", 18.9965, 72.8309),
    (8, "PR", "Prabhadevi", 19.0047, 72.8375),
    (9, "DDR", "Dadar", 19.0191, 72.8420),
    (10, "MRU", "Matunga Road", 19.0265, 72.8485),
    (11, "MM", "Mahim", 19.0358, 72.8535),
    (12, "BA", "Bandra", 19.0544, 72.8405),
    (13, "KHR", "Khar Road", 19.0667, 72.8365),
    (14, "STC", "Santacruz", 19.0847, 72.8418),
    (15, "VLP", "Vile Parle", 19.0990, 72.8435),
    (16, "ADH", "Andheri", 19.1197, 72.8465),
    (17, "JOS", "Jogeshwari", 19.1365, 72.8485),
    (18, "RMR", "Ram Mandir", 19.1520, 72.8505),
    (19, "GMN", "Goregaon", 19.1645, 72.8525),
    (20, "MLD", "Malad", 19.1865, 72.8555),
    (21, "KND", "Kandivali", 19.2035, 72.8585),
    (22, "BVI", "Borivali", 19.2305, 72.8610),
    (23, "DIC", "Dahisar", 19.2520, 72.8635),
    (24, "MIRA", "Mira Road", 19.2815, 72.8685),
    (25, "BYR", "Bhayandar", 19.3015, 72.8720),
    (26, "NIG", "Naigaon", 19.3355, 72.8785),
    (27, "VAS", "Vasai Road", 19.3685, 72.8855),
    (28, "NSP", "Nalasopara", 19.4185, 72.8925),
    (29, "VR", "Virar", 19.4555, 72.9025),
]

ROLES = [
    ("passenger", "Passenger", 10),
    ("volunteer", "Volunteer", 20),
    ("station_moderator", "Station Moderator", 30),
    ("station_manager", "Station Manager", 40),
    ("divisional_officer", "Divisional Officer", 50),
    ("railway_admin", "Railway Admin", 60),
    ("super_admin", "Super Admin", 70),
]

CATEGORIES = [
    ("station_infrastructure", "Station Infrastructure", None, "building-2", 3),
    ("platform_cleanliness", "Platform Cleanliness", "station_infrastructure", "sparkles", 3),
    ("dustbins_waste", "Dustbins / Waste", "station_infrastructure", "trash-2", 3),
    ("accessibility", "Accessibility", None, "accessibility", 4),
    ("lifts_escalators", "Lifts / Escalators", "accessibility", "arrow-up-down", 4),
    ("safety_security", "Safety & Security", None, "shield", 5),
    ("womens_safety", "Women's Safety", "safety_security", "heart", 5),
    ("train_coach", "Train & Coach", None, "train", 3),
    ("overcrowding", "Overcrowding", "train_coach", "users", 4),
    ("facilities", "Facilities", None, "wrench", 3),
    ("ticket_counter", "Ticket Counter", "facilities", "ticket", 3),
    ("operations", "Operations", None, "clock", 2),
    ("train_punctuality", "Train Punctuality", "operations", "timer", 2),
    ("other", "Other", None, "more-horizontal", 2),
]


def seed(session: Session) -> None:
    zone = session.execute(select(Zone).where(Zone.code == "WR")).scalar_one_or_none()
    if not zone:
        zone = Zone(code="WR", name="Western Railway", country_code="IN")
        session.add(zone)
        session.flush()

    division = session.execute(select(Division).where(Division.code == "MUM")).scalar_one_or_none()
    if not division:
        division = Division(zone_id=zone.id, code="MUM", name="Mumbai")
        session.add(division)
        session.flush()

    for code, name, level in ROLES:
        if not session.execute(select(Role).where(Role.code == code)).scalar_one_or_none():
            session.add(Role(code=code, name=name, level=level))

    parent_ids: dict[str, uuid.UUID] = {}
    for code, name, parent_code, icon, severity in CATEGORIES:
        if session.execute(select(IssueCategory).where(IssueCategory.code == code)).scalar_one_or_none():
            continue
        parent_id = parent_ids.get(parent_code) if parent_code else None
        cat = IssueCategory(
            code=code,
            name=name,
            parent_id=parent_id,
            icon=icon,
            default_severity=severity,
        )
        session.add(cat)
        session.flush()
        parent_ids[code] = cat.id

    for seq, code, name, lat, lng in STATIONS:
        exists = session.execute(select(Station).where(Station.code == code)).scalar_one_or_none()
        if exists:
            continue
        session.add(
            Station(
                division_id=division.id,
                zone_id=zone.id,
                code=code,
                name=name,
                sequence_order=seq,
                latitude=lat,
                longitude=lng,
            )
        )

    configs = {
        "duplicate_similarity_threshold": 0.82,
        "anonymous_daily_issue_limit": 3,
        "priority_weights": {
            "support": 0.25,
            "severity": 0.25,
            "fresh": 0.15,
            "trend": 0.20,
            "ai": 0.15,
        },
    }
    for key, value in configs.items():
        if not session.get(SystemConfig, key):
            session.add(SystemConfig(key=key, value=value))

    # --- Three product personas (demo OTP = 123456 in mock mode) ---
    def _ensure_role(user: User, role_code: str, *, location_type: str | None = None, location_id=None) -> None:
        role = session.execute(select(Role).where(Role.code == role_code)).scalar_one()
        existing = session.execute(
            select(UserRole).where(
                UserRole.user_id == user.id,
                UserRole.role_id == role.id,
                UserRole.revoked_at.is_(None),
            )
        ).scalar_one_or_none()
        if existing:
            if location_type and location_id:
                existing.location_type = location_type
                existing.location_id = location_id
            return
        session.add(
            UserRole(
                user_id=user.id,
                role_id=role.id,
                location_type=location_type,
                location_id=location_id,
            )
        )

    # 1) Main Admin — all stations
    main_hash = hash_value("+919999999999")
    main_admin = session.execute(select(User).where(User.mobile_hash == main_hash)).scalar_one_or_none()
    if not main_admin:
        main_admin = User(
            display_name="Main Admin",
            mobile_hash=main_hash,
            is_verified=True,
            is_active=True,
        )
        session.add(main_admin)
        session.flush()
    else:
        main_admin.display_name = "Main Admin"
        main_admin.is_verified = True
        main_admin.is_active = True
    _ensure_role(main_admin, "super_admin")

    # 2) Station Admin — Bandra only
    bandra = session.execute(select(Station).where(Station.code == "BA")).scalar_one_or_none()
    station_hash = hash_value("+919888888888")
    station_admin = session.execute(select(User).where(User.mobile_hash == station_hash)).scalar_one_or_none()
    if bandra:
        if not station_admin:
            station_admin = User(
                display_name="Bandra Station Admin",
                mobile_hash=station_hash,
                is_verified=True,
                is_active=True,
            )
            session.add(station_admin)
            session.flush()
        else:
            station_admin.display_name = "Bandra Station Admin"
            station_admin.is_verified = True
            station_admin.is_active = True
        _ensure_role(
            station_admin,
            "station_manager",
            location_type="station",
            location_id=bandra.id,
        )

    # 3) Passenger — normal user
    passenger_hash = hash_value("+919111111111")
    passenger = session.execute(select(User).where(User.mobile_hash == passenger_hash)).scalar_one_or_none()
    if not passenger:
        passenger = User(
            display_name="Passenger Demo",
            mobile_hash=passenger_hash,
            is_verified=True,
            is_active=True,
        )
        session.add(passenger)
        session.flush()
    else:
        passenger.display_name = "Passenger Demo"
        passenger.is_verified = True
        passenger.is_active = True
    _ensure_role(passenger, "passenger")

    # Assign demo passenger to Bandra so Station Admin can manage them
    if bandra and passenger:
        passenger.assigned_station_id = bandra.id
        passenger.mobile_last4 = "1111"
    if station_admin:
        station_admin.mobile_last4 = "8888"
        station_admin.assigned_station_id = bandra.id if bandra else None
    if main_admin:
        main_admin.mobile_last4 = "9999"

    session.commit()
    print(
        "Seed completed: 3 personas — "
        "Passenger +919111111111 | Station Admin (Bandra) +919888888888 | "
        "Main Admin +919999999999 (OTP 123456 in mock mode)"
    )


def main() -> None:
    engine = create_engine(settings.database_url_sync)
    with Session(engine) as session:
        seed(session)


if __name__ == "__main__":
    main()
