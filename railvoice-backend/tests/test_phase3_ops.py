"""Phase 3 unit tests — scope, SLA helpers, storage local path."""

from __future__ import annotations

import uuid

from app.core.config import Settings
from app.core.enums import LocationScope, RoleCode
from app.models.user import Role, User, UserRole
from app.services.scope import official_location_scopes
from app.services.storage import StorageService


def test_sla_hours_for_severity():
    s = Settings()
    assert s.sla_hours_for_severity(1) == 4
    assert s.sla_hours_for_severity(3) == 24
    assert s.sla_hours_for_severity(99) == 72


def test_storage_local_public_url(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("LOCAL_STORAGE_PATH", str(tmp_path))
    monkeypatch.setenv("PUBLIC_BASE_URL", "http://localhost:8000")
    from app.core import config

    monkeypatch.setattr(config.settings, "storage_backend", "local")
    monkeypatch.setattr(config.settings, "local_storage_path", str(tmp_path))
    monkeypatch.setattr(config.settings, "public_base_url", "http://localhost:8000")
    svc = StorageService()
    assert svc.public_url("issues/x/a.jpg") == "http://localhost:8000/media/issues/x/a.jpg"


def test_official_location_scopes_station():
    role = Role(id=uuid.uuid4(), code=RoleCode.STATION_MODERATOR.value, name="Mod", level=30)
    station_id = uuid.uuid4()
    user = User(id=uuid.uuid4(), display_name="Mod", is_active=True)
    user.roles = [
        UserRole(
            id=uuid.uuid4(),
            user_id=user.id,
            role_id=role.id,
            location_type=LocationScope.STATION.value,
            location_id=station_id,
            role=role,
        )
    ]
    scopes = official_location_scopes(user)
    assert scopes is not None
    assert station_id in scopes["station"]


def test_super_admin_unscoped():
    role = Role(id=uuid.uuid4(), code=RoleCode.SUPER_ADMIN.value, name="SA", level=70)
    user = User(id=uuid.uuid4(), display_name="SA", is_active=True)
    user.roles = [
        UserRole(id=uuid.uuid4(), user_id=user.id, role_id=role.id, role=role)
    ]
    assert official_location_scopes(user) is None
