from enum import StrEnum


class IssueStatus(StrEnum):
    CREATED = "created"
    AI_DUPLICATE_CHECK = "ai_duplicate_check"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    VERIFIED = "verified"
    ASSIGNED = "assigned"
    FORWARDED_STATION_MANAGER = "forwarded_station_manager"
    FORWARDED_DIVISION = "forwarded_division"
    FORWARDED_ZONE = "forwarded_zone"
    ACTION_STARTED = "action_started"
    WORK_IN_PROGRESS = "work_in_progress"
    WAITING_FOR_MATERIAL = "waiting_for_material"
    COMPLETED = "completed"
    VERIFIED_COMPLETE = "verified_complete"
    CLOSED = "closed"
    REJECTED = "rejected"
    SPAM = "spam"
    DUPLICATE_MERGED = "duplicate_merged"
    WITHDRAWN = "withdrawn"


TERMINAL_STATUSES = {
    IssueStatus.CLOSED,
    IssueStatus.REJECTED,
    IssueStatus.SPAM,
    IssueStatus.DUPLICATE_MERGED,
    IssueStatus.WITHDRAWN,
}

DUPLICATE_SEARCH_EXCLUDED = TERMINAL_STATUSES


class RoleCode(StrEnum):
    PASSENGER = "passenger"
    VOLUNTEER = "volunteer"
    STATION_MODERATOR = "station_moderator"
    STATION_MANAGER = "station_manager"
    DIVISIONAL_OFFICER = "divisional_officer"
    RAILWAY_ADMIN = "railway_admin"
    SUPER_ADMIN = "super_admin"


class LocationScope(StrEnum):
    ZONE = "zone"
    DIVISION = "division"
    STATION = "station"


class Visibility(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"


class TimelineEventType(StrEnum):
    CREATED = "created"
    DUPLICATE_CHECK = "duplicate_check"
    SUBMITTED = "submitted"
    STATUS_CHANGE = "status_change"
    ASSIGNED = "assigned"
    ESCALATED = "escalated"
    COMMENT_ADDED = "comment_added"
    SUPPORT_MILESTONE = "support_milestone"
    MERGED = "merged"
    RESOLVED = "resolved"
    CLOSED = "closed"


OFFICIAL_ROLES = {
    RoleCode.VOLUNTEER,
    RoleCode.STATION_MODERATOR,
    RoleCode.STATION_MANAGER,
    RoleCode.DIVISIONAL_OFFICER,
    RoleCode.RAILWAY_ADMIN,
    RoleCode.SUPER_ADMIN,
}

ROLE_LEVEL = {
    RoleCode.PASSENGER: 10,
    RoleCode.VOLUNTEER: 20,
    RoleCode.STATION_MODERATOR: 30,
    RoleCode.STATION_MANAGER: 40,
    RoleCode.DIVISIONAL_OFFICER: 50,
    RoleCode.RAILWAY_ADMIN: 60,
    RoleCode.SUPER_ADMIN: 70,
}
