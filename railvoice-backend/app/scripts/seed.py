"""Seed Western Railway corridor data with clean core entities for RailVoice."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import create_engine, select, delete
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_value
from app.models.issue import (
    Issue,
    IssuePhoto,
    Comment,
    IssueSupport,
    IssueTimelineEvent,
    SystemConfig,
)
from app.models.user import Role, User, UserRole, Notification
from app.models.location import Division, IssueCategory, Station, Zone

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
    # 1. Zone & Division
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

    # 2. Roles
    for code, name, level in ROLES:
        if not session.execute(select(Role).where(Role.code == code)).scalar_one_or_none():
            session.add(Role(code=code, name=name, level=level))

    # 3. Categories
    parent_ids: dict[str, uuid.UUID] = {}
    for code, name, parent_code, icon, severity in CATEGORIES:
        existing_cat = session.execute(select(IssueCategory).where(IssueCategory.code == code)).scalar_one_or_none()
        if existing_cat:
            parent_ids[code] = existing_cat.id
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

    # 4. Stations
    for seq, code, name, lat, lng in STATIONS:
        exists = session.execute(select(Station).where(Station.code == code)).scalar_one_or_none()
        if not exists:
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
    session.flush()

    # 5. Reset dynamic operational tables for a clean slate
    session.execute(delete(Comment))
    session.execute(delete(IssuePhoto))
    session.execute(delete(IssueSupport))
    session.execute(delete(IssueTimelineEvent))
    session.execute(delete(Issue))
    session.execute(delete(Notification))
    session.flush()

    # 6. Seed 3 Product Personas
    now = datetime.now(timezone.utc)
    super_admin_role = session.execute(select(Role).where(Role.code == "super_admin")).scalar_one()
    manager_role = session.execute(select(Role).where(Role.code == "station_manager")).scalar_one()
    passenger_role = session.execute(select(Role).where(Role.code == "passenger")).scalar_one()

    # Persona A: Western Railway Main Authority
    main_admin = session.execute(select(User).where(User.mobile_hash == hash_value("+919999999999"))).scalar_one_or_none()
    if not main_admin:
        main_admin = User(
            mobile_hash=hash_value("+919999999999"),
            mobile_masked="+91******9999",
            display_name="Western Railway Main Admin",
            is_verified=True,
            is_active=True,
        )
        session.add(main_admin)
        session.flush()
    session.execute(delete(UserRole).where(UserRole.user_id == main_admin.id))
    session.add(UserRole(user_id=main_admin.id, role_id=super_admin_role.id, scope_type="global", scope_id=None))

    # Persona B: Bandra Station Admin
    bandra_st = session.execute(select(Station).where(Station.code == "BA")).scalar_one()
    station_admin = session.execute(select(User).where(User.mobile_hash == hash_value("+919888888888"))).scalar_one_or_none()
    if not station_admin:
        station_admin = User(
            mobile_hash=hash_value("+919888888888"),
            mobile_masked="+91******8888",
            display_name="Bandra Station Admin",
            is_verified=True,
            is_active=True,
        )
        session.add(station_admin)
        session.flush()
    session.execute(delete(UserRole).where(UserRole.user_id == station_admin.id))
    session.add(UserRole(user_id=station_admin.id, role_id=manager_role.id, scope_type="station", scope_id=bandra_st.id))

    # Persona C: Daily Commuter
    commuter = session.execute(select(User).where(User.mobile_hash == hash_value("+919111111111"))).scalar_one_or_none()
    if not commuter:
        commuter = User(
            mobile_hash=hash_value("+919111111111"),
            mobile_masked="+91******1111",
            display_name="Rajesh Sharma (Commuter)",
            is_verified=True,
            is_active=True,
        )
        session.add(commuter)
        session.flush()
    session.execute(delete(UserRole).where(UserRole.user_id == commuter.id))
    session.add(UserRole(user_id=commuter.id, role_id=passenger_role.id, scope_type="global", scope_id=None))
    session.flush()

    # 7. Seed 3 Core Test Issues
    andheri_st = session.execute(select(Station).where(Station.code == "ADH")).scalar_one()
    churchgate_st = session.execute(select(Station).where(Station.code == "CCG")).scalar_one()
    clean_cat = session.execute(select(IssueCategory).where(IssueCategory.code == "platform_cleanliness")).scalar_one()
    lift_cat = session.execute(select(IssueCategory).where(IssueCategory.code == "lifts_escalators")).scalar_one()
    safety_cat = session.execute(select(IssueCategory).where(IssueCategory.code == "safety_security")).scalar_one()

    # Issue 1: Bandra Overflowing Garbage (Reviewed by Station Admin)
    i1 = Issue(
        id=uuid.uuid4(),
        issue_number="RV-WR-2026-000101",
        zone_id=zone.id,
        division_id=division.id,
        station_id=bandra_st.id,
        creator_id=commuter.id,
        category_id=clean_cat.id,
        title="Overflowing Waste Bins near Foot Overbridge on Platform 1",
        description="Garbage bins near the north FOB on Platform 1 are overflowing since early morning, causing foul smell and blocking passenger movement during peak hours.",
        status="action_started",
        severity=3,
        support_count=42,
        comment_count=1,
        is_emergency=False,
        is_public=True,
        created_at=now - timedelta(hours=6),
        updated_at=now - timedelta(hours=1),
    )
    session.add(i1)

    # Issue 2: Andheri Escalator Malfunction (Escalated to Division)
    i2 = Issue(
        id=uuid.uuid4(),
        issue_number="RV-WR-2026-000102",
        zone_id=zone.id,
        division_id=division.id,
        station_id=andheri_st.id,
        creator_id=commuter.id,
        category_id=lift_cat.id,
        title="Escalator Stopped on Platform 4/5 West Exit",
        description="The upward escalator on Platform 4/5 connecting to the west skywalk has abruptly stopped. Senior citizens and passengers with heavy luggage are facing immense difficulty.",
        status="forwarded_division",
        severity=4,
        support_count=89,
        comment_count=1,
        is_emergency=False,
        is_public=True,
        created_at=now - timedelta(hours=18),
        updated_at=now - timedelta(hours=2),
    )
    session.add(i2)

    # Issue 3: Churchgate Emergency Warning (High Upvotes / Emergency Flag)
    i3 = Issue(
        id=uuid.uuid4(),
        issue_number="RV-WR-2026-000103",
        zone_id=zone.id,
        division_id=division.id,
        station_id=churchgate_st.id,
        creator_id=commuter.id,
        category_id=safety_cat.id,
        title="Platform Edge Paver Tiles Broken & Loose at Coach 4 Stopping Mark",
        description="Broken tactiles and sharp dislodged paver blocks along platform edge 2. High tripping hazard during morning rush hour rush when alighting from local trains.",
        status="verified",
        severity=5,
        support_count=124,
        comment_count=1,
        is_emergency=True,
        is_public=True,
        created_at=now - timedelta(days=1),
        updated_at=now - timedelta(hours=3),
    )
    session.add(i3)
    session.flush()

    # Supports & Timeline Events for the 3 Issues
    for iss in [i1, i2, i3]:
        session.add(IssueSupport(issue_id=iss.id, user_id=commuter.id, created_at=iss.created_at))
        session.add(
            IssueTimelineEvent(
                issue_id=iss.id,
                event_type="submitted",
                from_status=None,
                to_status="submitted",
                actor_id=commuter.id,
                remarks="Problem submitted by citizen.",
                visibility="public",
                created_at=iss.created_at,
            )
        )

    # Timeline event for Bandra issue
    session.add(
        IssueTimelineEvent(
            issue_id=i1.id,
            event_type="status_change",
            from_status="submitted",
            to_status="action_started",
            actor_id=station_admin.id,
            remarks="Sanitation supervisor assigned. Cleaning in progress.",
            visibility="public",
            created_at=now - timedelta(hours=1),
        )
    )

    # Timeline event for Andheri escalated issue
    session.add(
        IssueTimelineEvent(
            issue_id=i2.id,
            event_type="escalated",
            from_status="verified",
            to_status="forwarded_division",
            actor_id=station_admin.id,
            remarks="Escalated to Mumbai Divisional Electrical Engineering team for motor inspection.",
            visibility="public",
            created_at=now - timedelta(hours=2),
        )
    )

    # Comments
    session.add(
        Comment(
            issue_id=i1.id,
            user_id=commuter.id,
            body="Thank you for taking action on Platform 1 garbage so quickly!",
            created_at=now - timedelta(minutes=45),
        )
    )
    session.add(
        Comment(
            issue_id=i2.id,
            user_id=commuter.id,
            body="Huge crowd backing up at Andheri west exit. Please repair this ASAP.",
            created_at=now - timedelta(hours=5),
        )
    )
    session.add(
        Comment(
            issue_id=i3.id,
            user_id=station_admin.id,
            body="Inspected on morning rounds. Barricade placed around the damaged edge.",
            created_at=now - timedelta(hours=2),
        )
    )

    # Notifications
    session.add(
        Notification(
            user_id=commuter.id,
            type="status_change",
            title="Bandra Issue In Progress",
            body="Your reported issue RV-WR-2026-000101 is now under active resolution.",
            issue_id=i1.id,
            is_read=False,
            created_at=now - timedelta(hours=1),
        )
    )
    session.add(
        Notification(
            user_id=main_admin.id,
            type="station_report",
            title="Escalated Issue from Andheri",
            body="Issue RV-WR-2026-000102 has been escalated to Division for electrical repair.",
            issue_id=i2.id,
            is_read=False,
            created_at=now - timedelta(hours=2),
        )
    )

    session.commit()
    print("Clean RailVoice database seed completed successfully!")


if __name__ == "__main__":
    engine = create_engine(settings.database_url_sync)
    with Session(engine) as session:
        seed(session)
