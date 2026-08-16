"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "zones",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=10), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("country_code", sa.String(length=2), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "roles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "issue_categories",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("parent_id", sa.UUID(), nullable=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("name_hi", sa.String(length=100), nullable=True),
        sa.Column("name_mr", sa.String(length=100), nullable=True),
        sa.Column("icon", sa.String(length=50), nullable=True),
        sa.Column("default_severity", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["parent_id"], ["issue_categories.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "divisions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("zone_id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["zone_id"], ["zones.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("zone_id", "code"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("mobile_hash", sa.String(length=64), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("google_id", sa.String(length=255), nullable=True),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("preferred_language", sa.String(length=5), nullable=True),
        sa.Column("is_anonymous", sa.Boolean(), nullable=True),
        sa.Column("anonymous_session_id", sa.UUID(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("anonymous_session_id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("google_id"),
        sa.UniqueConstraint("mobile_hash"),
    )
    op.create_table(
        "system_config",
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("key"),
    )
    op.create_table(
        "stations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("division_id", sa.UUID(), nullable=False),
        sa.Column("zone_id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=10), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("name_hi", sa.String(length=100), nullable=True),
        sa.Column("name_mr", sa.String(length=100), nullable=True),
        sa.Column("sequence_order", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["division_id"], ["divisions.id"]),
        sa.ForeignKeyConstraint(["zone_id"], ["zones.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "notifications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("issue_id", sa.UUID(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "otp_requests",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("mobile_hash", sa.String(length=64), nullable=False),
        sa.Column("otp_hash", sa.String(length=64), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_otp_requests_mobile_hash", "otp_requests", ["mobile_hash"])
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("family_id", sa.UUID(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_table(
        "user_roles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("role_id", sa.UUID(), nullable=False),
        sa.Column("location_type", sa.String(length=20), nullable=True),
        sa.Column("location_id", sa.UUID(), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "platforms",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("station_id", sa.UUID(), nullable=False),
        sa.Column("platform_number", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["station_id"], ["stations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("station_id", "platform_number"),
    )
    op.create_table(
        "issues",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("issue_number", sa.String(length=20), nullable=False),
        sa.Column("zone_id", sa.UUID(), nullable=False),
        sa.Column("division_id", sa.UUID(), nullable=False),
        sa.Column("station_id", sa.UUID(), nullable=False),
        sa.Column("platform_id", sa.UUID(), nullable=True),
        sa.Column("creator_id", sa.UUID(), nullable=True),
        sa.Column("category_id", sa.UUID(), nullable=True),
        sa.Column("subcategory_id", sa.UUID(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("embedding", sa.Text(), nullable=True),
        sa.Column("embedding_model", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.Integer(), nullable=True),
        sa.Column("support_count", sa.Integer(), nullable=True),
        sa.Column("comment_count", sa.Integer(), nullable=True),
        sa.Column("priority_score", sa.Numeric(8, 2), nullable=True),
        sa.Column("trending_score", sa.Numeric(8, 4), nullable=True),
        sa.Column("ai_priority_score", sa.Numeric(5, 4), nullable=True),
        sa.Column("spam_score", sa.Numeric(5, 4), nullable=True),
        sa.Column("is_emergency", sa.Boolean(), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=True),
        sa.Column("train_number", sa.String(length=10), nullable=True),
        sa.Column("coach_number", sa.String(length=10), nullable=True),
        sa.Column("latitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("longitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("merged_into_id", sa.UUID(), nullable=True),
        sa.Column("divergence_reason", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("edit_window_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["category_id"], ["issue_categories.id"]),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["division_id"], ["divisions.id"]),
        sa.ForeignKeyConstraint(["merged_into_id"], ["issues.id"]),
        sa.ForeignKeyConstraint(["platform_id"], ["platforms.id"]),
        sa.ForeignKeyConstraint(["station_id"], ["stations.id"]),
        sa.ForeignKeyConstraint(["subcategory_id"], ["issue_categories.id"]),
        sa.ForeignKeyConstraint(["zone_id"], ["zones.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("issue_number"),
    )
    op.create_index("idx_issues_station_priority", "issues", ["station_id", "priority_score"])
    op.create_index("idx_issues_created_at", "issues", ["created_at"])
    op.create_table(
        "comments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("issue_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("parent_id", sa.UUID(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_hidden", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["issue_id"], ["issues.id"]),
        sa.ForeignKeyConstraint(["parent_id"], ["comments.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "issue_photos",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("issue_id", sa.UUID(), nullable=False),
        sa.Column("uploader_id", sa.UUID(), nullable=True),
        sa.Column("storage_key", sa.String(length=500), nullable=False),
        sa.Column("mime_type", sa.String(length=50), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("thumbnail_key", sa.String(length=500), nullable=True),
        sa.Column("scan_status", sa.String(length=20), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["issue_id"], ["issues.id"]),
        sa.ForeignKeyConstraint(["uploader_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "issue_supports",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("issue_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["issue_id"], ["issues.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("issue_id", "user_id"),
    )
    op.create_table(
        "issue_timeline_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("issue_id", sa.UUID(), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("from_status", sa.String(length=50), nullable=True),
        sa.Column("to_status", sa.String(length=50), nullable=True),
        sa.Column("actor_id", sa.UUID(), nullable=True),
        sa.Column("actor_role", sa.String(length=50), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("visibility", sa.String(length=20), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["issue_id"], ["issues.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_timeline_issue_created", "issue_timeline_events", ["issue_id", "created_at"])


def downgrade() -> None:
    op.drop_table("issue_timeline_events")
    op.drop_table("issue_supports")
    op.drop_table("issue_photos")
    op.drop_table("comments")
    op.drop_table("issues")
    op.drop_table("platforms")
    op.drop_table("user_roles")
    op.drop_table("refresh_tokens")
    op.drop_table("otp_requests")
    op.drop_table("notifications")
    op.drop_table("stations")
    op.drop_table("system_config")
    op.drop_table("users")
    op.drop_table("divisions")
    op.drop_table("issue_categories")
    op.drop_table("roles")
    op.drop_table("zones")
