"""Seed Western Railway corridor data with clean demo entities for RailVoice."""

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
from app.models.user import (
    AuthAuditEvent,
    Notification,
    OtpRequest,
    RefreshToken,
    Role,
    User,
    UserManagementAudit,
    UserRole,
)
from app.models.location import Division, IssueCategory, Platform, Station, Zone

ZONES = [
    ("WR", "Western Railway", "IN"),
    ("CR", "Central Railway", "IN"),
    ("NR", "Northern Railway", "IN"),
]

DIVISIONS = [
    ("WR", "MUM", "Mumbai"),
    ("WR", "BRC", "Vadodara"),
    ("WR", "ADI", "Ahmedabad"),
]

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
    print("[seed] Clearing all existing data from tables...")
    # Clean tables in reverse dependency order
    session.execute(delete(Comment))
    session.execute(delete(IssuePhoto))
    session.execute(delete(IssueSupport))
    session.execute(delete(IssueTimelineEvent))
    session.execute(delete(Issue))
    session.execute(delete(Notification))
    session.execute(delete(RefreshToken))
    session.execute(delete(OtpRequest))
    session.execute(delete(AuthAuditEvent))
    session.execute(delete(UserManagementAudit))
    session.execute(delete(UserRole))
    session.execute(delete(User))
    session.execute(delete(Platform))
    session.execute(delete(Station))
    session.execute(delete(IssueCategory))
    session.execute(delete(Role))
    session.execute(delete(Division))
    session.execute(delete(Zone))
    session.flush()

    # 1. 3 Zones
    print("[seed] Seeding 3 Zones...")
    zone_map: dict[str, Zone] = {}
    for code, name, country in ZONES:
        z = Zone(code=code, name=name, country_code=country)
        session.add(z)
        zone_map[code] = z
    session.flush()

    # 2. 3 Divisions
    print("[seed] Seeding 3 Divisions...")
    div_map: dict[str, Division] = {}
    for z_code, d_code, d_name in DIVISIONS:
        d = Division(zone_id=zone_map[z_code].id, code=d_code, name=d_name)
        session.add(d)
        div_map[d_code] = d
    session.flush()

    # 3. Roles
    print("[seed] Seeding Roles...")
    role_map: dict[str, Role] = {}
    for code, name, level in ROLES:
        r = Role(code=code, name=name, level=level)
        session.add(r)
        role_map[code] = r
    session.flush()

    # 4. Categories
    print("[seed] Seeding Categories...")
    cat_map: dict[str, IssueCategory] = {}
    for code, name, parent_code, icon, severity in CATEGORIES:
        parent_id = cat_map[parent_code].id if parent_code and parent_code in cat_map else None
        cat = IssueCategory(
            code=code,
            name=name,
            parent_id=parent_id,
            icon=icon,
            default_severity=severity,
        )
        session.add(cat)
        session.flush()
        cat_map[code] = cat

    # 5. Stations (Churchgate to Virar)
    print("[seed] Seeding 28 Corridor Stations...")
    st_map: dict[str, Station] = {}
    mum_div = div_map["MUM"]
    wr_zone = zone_map["WR"]
    for seq, code, name, lat, lng in STATIONS:
        st = Station(
            division_id=mum_div.id,
            zone_id=wr_zone.id,
            code=code,
            name=name,
            sequence_order=seq,
            latitude=lat,
            longitude=lng,
        )
        session.add(st)
        st_map[code] = st
    session.flush()

    # 6. 3 Platforms for demo
    print("[seed] Seeding 3 Demo Platforms...")
    p1 = Platform(station_id=st_map["BA"].id, platform_number=1, name="Platform 1 (Slow / Up)")
    p2 = Platform(station_id=st_map["ADH"].id, platform_number=4, name="Platform 4 (Fast / Down)")
    p3 = Platform(station_id=st_map["CCG"].id, platform_number=2, name="Platform 2 (Terminal)")
    session.add_all([p1, p2, p3])
    session.flush()

    # 7. 3 Demo Personas (Users)
    print("[seed] Seeding 3 Demo Personas...")
    now = datetime.now(timezone.utc)

    # Persona A: Western Railway Main Authority / Super Admin
    main_admin = User(
        mobile_hash=hash_value("+919999999999"),
        mobile_last4="9999",
        display_name="Western Railway Main Admin",
        is_verified=True,
        is_active=True,
    )
    # Persona B: Bandra Station Admin
    station_admin = User(
        mobile_hash=hash_value("+919888888888"),
        mobile_last4="8888",
        display_name="Bandra Station Admin",
        assigned_station_id=st_map["BA"].id,
        is_verified=True,
        is_active=True,
    )
    # Persona C: Daily Commuter Passenger
    commuter = User(
        mobile_hash=hash_value("+919111111111"),
        mobile_last4="1111",
        display_name="Rajesh Sharma (Commuter)",
        is_verified=True,
        is_active=True,
    )
    session.add_all([main_admin, station_admin, commuter])
    session.flush()

    # User Roles
    session.add(UserRole(user_id=main_admin.id, role_id=role_map["super_admin"].id, location_type=None, location_id=None))
    session.add(UserRole(user_id=station_admin.id, role_id=role_map["station_manager"].id, location_type="station", location_id=st_map["BA"].id))
    session.add(UserRole(user_id=commuter.id, role_id=role_map["passenger"].id, location_type=None, location_id=None))
    session.flush()

    # 8. 3 Demo Issues
    print("[seed] Seeding 3 Core Demo Issues...")
    # Issue 1: Bandra Waste Overflow (Reviewed & Action Started)
    i1 = Issue(
        id=uuid.uuid4(),
        issue_number="RV-WR-2026-000101",
        zone_id=wr_zone.id,
        division_id=mum_div.id,
        station_id=st_map["BA"].id,
        platform_id=p1.id,
        creator_id=commuter.id,
        category_id=cat_map["platform_cleanliness"].id,
        title="Overflowing Waste Bins near Foot Overbridge on Platform 1",
        description="Garbage bins near the north FOB on Platform 1 are overflowing since early morning, causing foul smell and blocking passenger movement during peak hours.",
        status="action_started",
        severity=3,
        support_count=42,
        comment_count=1,
        priority_score=45.50,
        trending_score=3.2000,
        is_emergency=False,
        is_public=True,
        created_at=now - timedelta(hours=6),
        updated_at=now - timedelta(hours=1),
    )

    # Issue 2: Andheri Escalator Stoppage (Escalated to Division)
    i2 = Issue(
        id=uuid.uuid4(),
        issue_number="RV-WR-2026-000102",
        zone_id=wr_zone.id,
        division_id=mum_div.id,
        station_id=st_map["ADH"].id,
        platform_id=p2.id,
        creator_id=commuter.id,
        category_id=cat_map["lifts_escalators"].id,
        title="Escalator Stopped on Platform 4/5 West Exit",
        description="The upward escalator on Platform 4/5 connecting to the west skywalk has abruptly stopped. Senior citizens and passengers with heavy luggage are facing immense difficulty.",
        status="forwarded_division",
        severity=4,
        support_count=89,
        comment_count=1,
        priority_score=78.25,
        trending_score=5.8000,
        is_emergency=False,
        is_public=True,
        created_at=now - timedelta(hours=18),
        updated_at=now - timedelta(hours=2),
    )

    # Issue 3: Churchgate Loose Paver Hazard (Verified / Urgent Safety Hazard)
    i3 = Issue(
        id=uuid.uuid4(),
        issue_number="RV-WR-2026-000103",
        zone_id=wr_zone.id,
        division_id=mum_div.id,
        station_id=st_map["CCG"].id,
        platform_id=p3.id,
        creator_id=commuter.id,
        category_id=cat_map["safety_security"].id,
        title="Platform Edge Paver Tiles Broken & Loose at Coach 4 Stopping Mark",
        description="Broken tactiles and sharp dislodged paver blocks along platform edge 2. High tripping hazard during morning rush hour rush when alighting from local trains.",
        status="verified",
        severity=5,
        support_count=124,
        comment_count=1,
        priority_score=96.00,
        trending_score=9.4500,
        is_emergency=True,
        is_public=True,
        created_at=now - timedelta(days=1),
        updated_at=now - timedelta(hours=3),
    )
    session.add_all([i1, i2, i3])
    session.flush()

    # 9. 3 Upvote Supports
    print("[seed] Seeding 3 Issue Supports...")
    session.add(IssueSupport(issue_id=i1.id, user_id=commuter.id, created_at=i1.created_at))
    session.add(IssueSupport(issue_id=i2.id, user_id=commuter.id, created_at=i2.created_at))
    session.add(IssueSupport(issue_id=i3.id, user_id=commuter.id, created_at=i3.created_at))

    # 10. 3 Timeline Progression Events
    print("[seed] Seeding 3 Timeline Events...")
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
    session.add(
        IssueTimelineEvent(
            issue_id=i3.id,
            event_type="submitted",
            from_status=None,
            to_status="submitted",
            actor_id=commuter.id,
            remarks="Grievance reported by passenger with urgent safety flag.",
            visibility="public",
            created_at=i3.created_at,
        )
    )

    # 11. 3 Comments
    print("[seed] Seeding 3 Comments...")
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
            body="Inspected on morning rounds. Caution barricade placed around the damaged edge.",
            created_at=now - timedelta(hours=2),
        )
    )

    # 12. 3 Notifications
    print("[seed] Seeding 3 Notifications...")
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
    session.add(
        Notification(
            user_id=station_admin.id,
            type="urgent_hazard",
            title="Churchgate Paver Tile Alert",
            body="Urgent passenger hazard reported on Platform 2 edge.",
            issue_id=i3.id,
            is_read=False,
            created_at=now - timedelta(hours=3),
        )
    )

    session.commit()
    print("[seed] Complete: Clean RailVoice database seeded with 3 demo entries per domain table!")


if __name__ == "__main__":
    engine = create_engine(settings.database_url_sync)
    with Session(engine) as session:
        seed(session)
