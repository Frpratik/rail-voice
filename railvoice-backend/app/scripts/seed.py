"""Seed Western Railway corridor data with exactly 3 clean test entries per domain table."""

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
    IssueFeedback,
    SystemConfig,
)
from app.models.emergency import EmergencyAlert
from app.models.dispatch import WorkforceStaff, DispatchAssignment
from app.models.vendor import VendorContract, VendorPenaltyNote
from app.models.gamification import UserReputation
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

    # 5. System Config
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

    # 6. Wipe existing transactional/dynamic data cleanly
    session.execute(delete(DispatchAssignment))
    session.execute(delete(WorkforceStaff))
    session.execute(delete(VendorPenaltyNote))
    session.execute(delete(VendorContract))
    session.execute(delete(EmergencyAlert))
    session.execute(delete(Notification))
    session.execute(delete(UserReputation))
    session.execute(delete(IssueFeedback))
    session.execute(delete(Comment))
    session.execute(delete(IssuePhoto))
    session.execute(delete(IssueSupport))
    session.execute(delete(IssueTimelineEvent))
    session.execute(delete(Issue))
    session.flush()

    # 7. Helper for role assignment
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

    # 8. Seed exactly 3 Core Personas
    bandra = session.execute(select(Station).where(Station.code == "BA")).scalar_one()
    andheri = session.execute(select(Station).where(Station.code == "ADH")).scalar_one()
    churchgate = session.execute(select(Station).where(Station.code == "CCG")).scalar_one()

    # 1) Main Admin
    main_hash = hash_value("+919999999999")
    main_admin = session.execute(select(User).where(User.mobile_hash == main_hash)).scalar_one_or_none()
    if not main_admin:
        main_admin = User(
            display_name="Main Admin",
            mobile_hash=main_hash,
            mobile_last4="9999",
            is_verified=True,
            is_active=True,
        )
        session.add(main_admin)
        session.flush()
    _ensure_role(main_admin, "super_admin")

    # 2) Station Admin (Bandra)
    station_hash = hash_value("+919888888888")
    station_admin = session.execute(select(User).where(User.mobile_hash == station_hash)).scalar_one_or_none()
    if not station_admin:
        station_admin = User(
            display_name="Bandra Station Admin",
            mobile_hash=station_hash,
            mobile_last4="8888",
            assigned_station_id=bandra.id,
            is_verified=True,
            is_active=True,
        )
        session.add(station_admin)
        session.flush()
    _ensure_role(
        station_admin,
        "station_manager",
        location_type="station",
        location_id=bandra.id,
    )

    # 3) Passenger Demo
    passenger_hash = hash_value("+919111111111")
    passenger = session.execute(select(User).where(User.mobile_hash == passenger_hash)).scalar_one_or_none()
    if not passenger:
        passenger = User(
            display_name="Passenger Demo",
            mobile_hash=passenger_hash,
            mobile_last4="1111",
            assigned_station_id=bandra.id,
            is_verified=True,
            is_active=True,
        )
        session.add(passenger)
        session.flush()
    _ensure_role(passenger, "passenger")
    session.flush()

    # 9. Seed exactly 3 Issues
    cat_infra = session.execute(select(IssueCategory).where(IssueCategory.code == "station_infrastructure")).scalar_one()
    cat_clean = session.execute(select(IssueCategory).where(IssueCategory.code == "platform_cleanliness")).scalar_one()
    cat_safety = session.execute(select(IssueCategory).where(IssueCategory.code == "safety_security")).scalar_one()

    now = datetime.now(timezone.utc)

    issue1 = Issue(
        issue_number="RV-WR-2026-000101",
        zone_id=zone.id,
        division_id=division.id,
        station_id=bandra.id,
        creator_id=passenger.id,
        category_id=cat_clean.id,
        title="Overflowing dustbins and water leakage near FOB",
        description="Garbage bins overflowing beside foot over bridge stairs on Bandra Platform 2.",
        status="submitted",
        severity=3,
        support_count=18,
        comment_count=1,
        priority_score=82.5,
        trending_score=4.2,
        is_emergency=False,
        is_public=True,
        created_at=now - timedelta(hours=3),
    )

    issue2 = Issue(
        issue_number="RV-WR-2026-000102",
        zone_id=zone.id,
        division_id=division.id,
        station_id=andheri.id,
        creator_id=passenger.id,
        category_id=cat_infra.id,
        title="Digital train indicator board flickering at main concourse",
        description="The central overhead display board on Platform 3 is flickering and unreadable.",
        status="verified",
        severity=3,
        support_count=9,
        comment_count=1,
        priority_score=74.0,
        trending_score=2.8,
        is_emergency=False,
        is_public=True,
        created_at=now - timedelta(hours=6),
    )

    issue3 = Issue(
        issue_number="RV-WR-2026-000103",
        zone_id=zone.id,
        division_id=division.id,
        station_id=churchgate.id,
        creator_id=passenger.id,
        category_id=cat_safety.id,
        title="Emergency SOS help booth light malfunctioning",
        description="The SOS station alert indicator lamp is dim and unresponsive on Platform 1.",
        status="action_started",
        severity=5,
        support_count=32,
        comment_count=1,
        priority_score=95.0,
        trending_score=8.5,
        is_emergency=True,
        is_public=True,
        created_at=now - timedelta(hours=1),
    )

    session.add_all([issue1, issue2, issue3])
    session.flush()

    # 10. Seed exactly 3 Comments
    c1 = Comment(
        issue_id=issue1.id,
        user_id=station_admin.id,
        body="Station housekeeping supervisor notified. Plumber and cleaning crew assigned.",
        created_at=now - timedelta(hours=2),
    )
    c2 = Comment(
        issue_id=issue2.id,
        user_id=main_admin.id,
        body="Electrical engineering team inspected the display controller on site.",
        created_at=now - timedelta(hours=4),
    )
    c3 = Comment(
        issue_id=issue3.id,
        user_id=station_admin.id,
        body="RPF duty officer tested beacon wiring. Resolution underway.",
        created_at=now - timedelta(minutes=30),
    )
    session.add_all([c1, c2, c3])

    # 11. Seed exactly 3 Timeline Events
    t1 = IssueTimelineEvent(
        issue_id=issue1.id,
        event_type="created",
        to_status="submitted",
        actor_id=passenger.id,
        actor_role="passenger",
        remarks="Grievance submitted by commuter.",
        created_at=now - timedelta(hours=3),
    )
    t2 = IssueTimelineEvent(
        issue_id=issue2.id,
        event_type="status_change",
        from_status="submitted",
        to_status="verified",
        actor_id=station_admin.id,
        actor_role="station_manager",
        remarks="Verified by Station Duty Officer.",
        created_at=now - timedelta(hours=5),
    )
    t3 = IssueTimelineEvent(
        issue_id=issue3.id,
        event_type="status_change",
        from_status="verified",
        to_status="action_started",
        actor_id=main_admin.id,
        actor_role="super_admin",
        remarks="Emergency inspection dispatched.",
        created_at=now - timedelta(minutes=45),
    )
    session.add_all([t1, t2, t3])

    # 12. Seed exactly 3 Emergency Alerts
    e1 = EmergencyAlert(
        station_id=bandra.id,
        issuer_id=main_admin.id,
        severity="critical",
        title="Platform 1 Overhead Maintenance",
        message="Caution: Platform 1 track safety inspection active. Please use FOB for Platform 2.",
        is_active=True,
        expires_at=now + timedelta(hours=24),
    )
    e2 = EmergencyAlert(
        station_id=andheri.id,
        issuer_id=station_admin.id,
        severity="warning",
        title="Escalator 2 Maintenance at Andheri West",
        message="Escalator undergoing scheduled overhaul. Lifts are fully operational.",
        is_active=True,
        expires_at=now + timedelta(hours=12),
    )
    e3 = EmergencyAlert(
        station_id=churchgate.id,
        issuer_id=main_admin.id,
        severity="info",
        title="Corridor Fast Local Schedule",
        message="Peak hour fast suburban services running on regular timetable.",
        is_active=True,
        expires_at=now + timedelta(hours=8),
    )
    session.add_all([e1, e2, e3])

    # 13. Seed exactly 3 Workforce Staff Members
    w1 = WorkforceStaff(
        full_name="Rajesh Sharma",
        skill_category="electrical",
        contact_number="+919876000001",
        assigned_station_id=andheri.id,
        status="available",
        shift_start="08:00",
        shift_end="16:00",
        is_active=True,
    )
    w2 = WorkforceStaff(
        full_name="Sunil Patil",
        skill_category="housekeeping",
        contact_number="+919876000002",
        assigned_station_id=bandra.id,
        status="available",
        shift_start="06:00",
        shift_end="14:00",
        is_active=True,
    )
    w3 = WorkforceStaff(
        full_name="Inspector Vikram Singh",
        skill_category="safety",
        contact_number="+919876000003",
        assigned_station_id=churchgate.id,
        status="available",
        shift_start="14:00",
        shift_end="22:00",
        is_active=True,
    )
    session.add_all([w1, w2, w3])

    # 14. Seed exactly 3 Vendor Contracts
    v1 = VendorContract(
        vendor_name="CleanRail Facility Services Pvt Ltd",
        contract_code="VND-WR-001",
        station_id=bandra.id,
        category_id=cat_clean.id,
        penalty_per_sla_hour=500.0,
        max_penalty_cap=50000.0,
        is_active=True,
    )
    v2 = VendorContract(
        vendor_name="Sparkline Electricals & Infrastructure",
        contract_code="VND-WR-002",
        station_id=andheri.id,
        category_id=cat_infra.id,
        penalty_per_sla_hour=1000.0,
        max_penalty_cap=100000.0,
        is_active=True,
    )
    v3 = VendorContract(
        vendor_name="Apex Safety Systems & Security Tech",
        contract_code="VND-WR-003",
        station_id=churchgate.id,
        category_id=cat_safety.id,
        penalty_per_sla_hour=1500.0,
        max_penalty_cap=150000.0,
        is_active=True,
    )
    session.add_all([v1, v2, v3])
    session.flush()

    # 15. Seed exactly 3 Vendor Penalty Notes
    p1 = VendorPenaltyNote(
        contract_id=v1.id,
        issue_id=issue1.id,
        penalty_amount=2500.0,
        clause_reference="SLA Cl. 4.2 - Delay in waste clearance beyond SLA target",
        status="pending_review",
    )
    p2 = VendorPenaltyNote(
        contract_id=v2.id,
        issue_id=issue2.id,
        penalty_amount=4000.0,
        clause_reference="SLA Cl. 6.1 - Unscheduled display unit downtime",
        status="approved",
    )
    p3 = VendorPenaltyNote(
        contract_id=v3.id,
        issue_id=issue3.id,
        penalty_amount=6000.0,
        clause_reference="SLA Cl. 8.3 - Safety beacon inspection SLA breach",
        status="pending_review",
    )
    session.add_all([p1, p2, p3])

    # 16. Seed exactly 3 User Reputation Records (Leaderboard)
    r1 = UserReputation(
        user_id=main_admin.id,
        points=450,
        tier="platinum",
        badge_slugs=["civic_champion", "speed_resolver", "verified_hero"],
        reports_count=15,
        verifications_count=12,
    )
    r2 = UserReputation(
        user_id=station_admin.id,
        points=280,
        tier="gold",
        badge_slugs=["civic_champion", "speed_resolver"],
        reports_count=9,
        verifications_count=8,
    )
    r3 = UserReputation(
        user_id=passenger.id,
        points=120,
        tier="silver",
        badge_slugs=["first_reporter"],
        reports_count=3,
        verifications_count=2,
    )
    session.add_all([r1, r2, r3])

    # 17. Seed exactly 3 Notifications
    n1 = Notification(
        user_id=main_admin.id,
        type="system",
        title="Corridor AI Summary Ready",
        body="Daily Western Railway corridor AI analytics pack is ready for review.",
        is_read=False,
    )
    n2 = Notification(
        user_id=station_admin.id,
        type="assignment",
        title="New Grievance at Bandra",
        body="Report RV-WR-2026-000101 assigned to Bandra station queue.",
        issue_id=issue1.id,
        is_read=False,
    )
    n3 = Notification(
        user_id=passenger.id,
        type="status_update",
        title="Grievance Verified",
        body="Your issue RV-WR-2026-000101 has been verified by the station duty officer.",
        issue_id=issue1.id,
        is_read=True,
    )
    session.add_all([n1, n2, n3])

    session.commit()
    print("Clean 3-entry database seeding completed successfully!")


def main() -> None:
    engine = create_engine(settings.database_url_sync)
    with Session(engine) as session:
        seed(session)


if __name__ == "__main__":
    main()
