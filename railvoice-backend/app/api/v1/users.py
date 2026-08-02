"""User management + self-service profile APIs."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_main_admin, require_user_manager
from app.models.user import User
from app.schemas.common import Envelope, Meta, UserOut
from app.schemas.mappers import user_to_out
from app.services import user_management as um
from app.services.personas import PERSONA_MAIN_ADMIN, user_persona
from app.services.storage import storage_service

admin_users_router = APIRouter(prefix="/admin/users", tags=["User Management"])
me_router = APIRouter(prefix="/me", tags=["My Profile"])


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


class UserUpdateBody(BaseModel):
    display_name: str | None = Field(None, min_length=2, max_length=100)
    email: EmailStr | None = None
    preferred_language: str | None = Field(None, max_length=5)


class LockBody(BaseModel):
    reason: str | None = Field(None, max_length=255)


class AssignRoleBody(BaseModel):
    role_code: str = Field(..., pattern=r"^(passenger|station_manager|super_admin)$")
    station_id: uuid.UUID | None = None


class AssignStationBody(BaseModel):
    station_id: uuid.UUID | None = None


class ChangePasswordBody(BaseModel):
    current_password: str | None = None
    new_password: str = Field(..., min_length=8, max_length=128)


class BulkIdsBody(BaseModel):
    user_ids: list[uuid.UUID] = Field(..., min_length=1, max_length=50)
    reason: str | None = None


class CreateUserBody(BaseModel):
    mobile: str = Field(..., pattern=r"^\+91\d{10}$")
    display_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr | None = None
    role_code: str = Field("passenger", pattern=r"^(passenger|station_manager|super_admin)$")
    station_id: uuid.UUID | None = None
    generate_password: bool = True


@admin_users_router.get("")
async def list_users(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    actor: Annotated[User, Depends(require_user_manager)],
    q: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    role: str | None = None,
    station_id: uuid.UUID | None = None,
    sort: str = "created_at",
    order: str = "desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    include_deleted: bool = False,
) -> Envelope[dict]:
    try:
        data = await um.list_users(
            db,
            actor,
            q=q,
            status_filter=status_filter,
            role=role,
            station_id=station_id,
            sort=sort,
            order=order,
            page=page,
            page_size=page_size,
            include_deleted=include_deleted and user_persona(actor) == PERSONA_MAIN_ADMIN,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return Envelope(data=data, meta=Meta())


@admin_users_router.post("")
async def create_user(
    body: CreateUserBody,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    actor: Annotated[User, Depends(require_main_admin)],
) -> Envelope[dict]:
    try:
        user, temp = await um.create_user(
            db,
            actor,
            mobile=body.mobile,
            display_name=body.display_name,
            email=str(body.email) if body.email else None,
            role_code=body.role_code,
            station_id=body.station_id,
            generate_password=body.generate_password,
            ip=_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
        )
        payload = await um.serialize_user_admin(db, user)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Envelope(
        data={"user": payload, "temporary_password": temp},
        meta=Meta(),
    )


@admin_users_router.post("/bulk/deactivate")
async def bulk_deactivate(
    body: BulkIdsBody,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    actor: Annotated[User, Depends(require_user_manager)],
) -> Envelope[dict]:
    updated = 0
    errors: list[str] = []
    for uid in body.user_ids:
        try:
            user = await um.get_user_for_admin(db, actor, uid)
            await um.set_active(
                db,
                actor,
                user,
                active=False,
                ip=_client_ip(request),
                user_agent=request.headers.get("User-Agent"),
            )
            updated += 1
        except Exception as exc:
            errors.append(f"{uid}: {exc}")
    return Envelope(data={"updated": updated, "errors": errors}, meta=Meta())


@admin_users_router.post("/bulk/lock")
async def bulk_lock(
    body: BulkIdsBody,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    actor: Annotated[User, Depends(require_user_manager)],
) -> Envelope[dict]:
    updated = 0
    errors: list[str] = []
    for uid in body.user_ids:
        try:
            user = await um.get_user_for_admin(db, actor, uid)
            await um.set_locked(
                db,
                actor,
                user,
                locked=True,
                reason=body.reason,
                ip=_client_ip(request),
                user_agent=request.headers.get("User-Agent"),
            )
            updated += 1
        except Exception as exc:
            errors.append(f"{uid}: {exc}")
    return Envelope(data={"updated": updated, "errors": errors}, meta=Meta())


@admin_users_router.get("/{user_id}")
async def get_user(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    actor: Annotated[User, Depends(require_user_manager)],
) -> Envelope[dict]:
    try:
        user = await um.get_user_for_admin(db, actor, user_id)
        payload = await um.serialize_user_admin(db, user)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return Envelope(data=payload, meta=Meta())


@admin_users_router.patch("/{user_id}")
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdateBody,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    actor: Annotated[User, Depends(require_user_manager)],
) -> Envelope[dict]:
    try:
        user = await um.get_user_for_admin(db, actor, user_id)
        user = await um.update_user_profile_fields(
            db,
            actor,
            user,
            display_name=body.display_name,
            email=str(body.email) if body.email else None,
            preferred_language=body.preferred_language,
            ip=_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
        )
        payload = await um.serialize_user_admin(db, user)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return Envelope(data=payload, meta=Meta())


@admin_users_router.post("/{user_id}/activate")
async def activate_user(
    user_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    actor: Annotated[User, Depends(require_user_manager)],
) -> Envelope[dict]:
    return await _toggle_active(user_id, True, request, db, actor)


@admin_users_router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    actor: Annotated[User, Depends(require_user_manager)],
) -> Envelope[dict]:
    return await _toggle_active(user_id, False, request, db, actor)


async def _toggle_active(user_id, active, request, db, actor) -> Envelope[dict]:
    try:
        user = await um.get_user_for_admin(db, actor, user_id)
        user = await um.set_active(
            db,
            actor,
            user,
            active=active,
            ip=_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
        )
        return Envelope(data=await um.serialize_user_admin(db, user), meta=Meta())
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@admin_users_router.post("/{user_id}/lock")
async def lock_user(
    user_id: uuid.UUID,
    body: LockBody,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    actor: Annotated[User, Depends(require_user_manager)],
) -> Envelope[dict]:
    try:
        user = await um.get_user_for_admin(db, actor, user_id)
        user = await um.set_locked(
            db,
            actor,
            user,
            locked=True,
            reason=body.reason,
            ip=_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
        )
        return Envelope(data=await um.serialize_user_admin(db, user), meta=Meta())
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@admin_users_router.post("/{user_id}/unlock")
async def unlock_user(
    user_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    actor: Annotated[User, Depends(require_user_manager)],
) -> Envelope[dict]:
    try:
        user = await um.get_user_for_admin(db, actor, user_id)
        user = await um.set_locked(
            db,
            actor,
            user,
            locked=False,
            ip=_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
        )
        return Envelope(data=await um.serialize_user_admin(db, user), meta=Meta())
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@admin_users_router.post("/{user_id}/reset-password")
async def reset_password(
    user_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    actor: Annotated[User, Depends(require_user_manager)],
) -> Envelope[dict]:
    try:
        user = await um.get_user_for_admin(db, actor, user_id)
        temp = await um.reset_password(
            db,
            actor,
            user,
            ip=_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
        )
        return Envelope(
            data={"temporary_password": temp, "user": await um.serialize_user_admin(db, user)},
            meta=Meta(),
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@admin_users_router.post("/{user_id}/assign-role")
async def assign_role(
    user_id: uuid.UUID,
    body: AssignRoleBody,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    actor: Annotated[User, Depends(require_main_admin)],
) -> Envelope[dict]:
    try:
        user = await um.get_user_for_admin(db, actor, user_id)
        user = await um.assign_role(
            db,
            actor,
            user,
            role_code=body.role_code,
            station_id=body.station_id,
            ip=_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
        )
        # reload roles
        user = await um.get_user_for_admin(db, actor, user_id)
        return Envelope(data=await um.serialize_user_admin(db, user), meta=Meta())
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@admin_users_router.post("/{user_id}/assign-station")
async def assign_station(
    user_id: uuid.UUID,
    body: AssignStationBody,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    actor: Annotated[User, Depends(require_main_admin)],
) -> Envelope[dict]:
    try:
        user = await um.get_user_for_admin(db, actor, user_id)
        user = await um.assign_station(
            db,
            actor,
            user,
            station_id=body.station_id,
            ip=_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
        )
        return Envelope(data=await um.serialize_user_admin(db, user), meta=Meta())
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@admin_users_router.delete("/{user_id}")
async def soft_delete(
    user_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    actor: Annotated[User, Depends(require_main_admin)],
) -> Envelope[dict]:
    try:
        user = await um.get_user_for_admin(db, actor, user_id)
        user = await um.soft_delete_user(
            db,
            actor,
            user,
            ip=_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
        )
        return Envelope(data=await um.serialize_user_admin(db, user), meta=Meta())
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@admin_users_router.post("/{user_id}/restore")
async def restore(
    user_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    actor: Annotated[User, Depends(require_main_admin)],
) -> Envelope[dict]:
    try:
        user = await um.get_user_for_admin(db, actor, user_id)
        user = await um.restore_user(
            db,
            actor,
            user,
            ip=_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
        )
        return Envelope(data=await um.serialize_user_admin(db, user), meta=Meta())
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@admin_users_router.get("/{user_id}/audits")
async def user_audits(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    actor: Annotated[User, Depends(require_user_manager)],
    limit: int = Query(50, ge=1, le=200),
) -> Envelope[dict]:
    try:
        items = await um.list_audits_for_user(db, actor, user_id, limit=limit)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return Envelope(data={"items": items}, meta=Meta())


# ---- Self-service (/me) ----


@me_router.get("")
async def get_me(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Envelope[dict]:
    payload = await um.serialize_user_admin(db, user)
    return Envelope(data=payload, meta=Meta())


@me_router.patch("")
async def update_me(
    body: UserUpdateBody,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Envelope[UserOut]:
    try:
        updated = await um.update_user_profile_fields(
            db,
            user,
            user,
            display_name=body.display_name,
            email=str(body.email) if body.email else None,
            preferred_language=body.preferred_language,
            ip=_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return Envelope(data=user_to_out(updated), meta=Meta())


@me_router.post("/change-password")
async def change_password(
    body: ChangePasswordBody,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Envelope[dict]:
    try:
        await um.change_own_password(
            db,
            user,
            current_password=body.current_password,
            new_password=body.new_password,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Envelope(data={"message": "Password updated"}, meta=Meta())


@me_router.post("/avatar")
async def upload_avatar(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(...),
) -> Envelope[dict]:
    data = await file.read()
    if len(data) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Avatar must be under 2MB")
    content_type = file.content_type or ""
    if content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, or WebP allowed")
    key = storage_service.build_key(issue_id=user.id, filename=file.filename or "avatar.jpg")
    # reuse issues/ path shape; fine for local/s3
    await storage_service.save_bytes(key, data, content_type)
    user.avatar_url = storage_service.public_url(key)
    await um.write_user_audit(
        db,
        action="user.updated",
        actor=user,
        target=user,
        previous={},
        new={"avatar_url": user.avatar_url},
    )
    await db.flush()
    return Envelope(data={"avatar_url": user.avatar_url}, meta=Meta())
