import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.core.rate_limit import check_mobile_otp_limit
from app.core.security import hash_value
from app.models.user import RefreshToken, User, UserRole
from app.schemas.common import (
    AnonymousSessionOut,
    Envelope,
    GoogleAuthRequest,
    Meta,
    OTPRequestBody,
    OTPVerifyBody,
    RefreshRequest,
    TokenResponse,
)
from app.schemas.mappers import user_to_out
from app.services.audit import write_auth_audit, write_auth_audit_committed
from app.services.issue_service import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def _set_refresh_cookie(response: Response, refresh_value: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh_value,
        httponly=True,
        secure=settings.is_production or not settings.debug,
        samesite="lax",
        path="/api/v1/auth",
        max_age=settings.refresh_token_expire_days * 86400,
    )


async def _token_envelope(db: AsyncSession, user: User, response: Response) -> Envelope[TokenResponse]:
    user_result = await db.execute(
        select(User)
        .options(selectinload(User.roles).selectinload(UserRole.role))
        .where(User.id == user.id)
    )
    user = user_result.scalar_one()
    access_token, refresh_value, _ = await auth_service.issue_tokens(db, user)
    _set_refresh_cookie(response, refresh_value)
    return Envelope(
        data=TokenResponse(
            access_token=access_token,
            expires_in=settings.access_token_expire_minutes * 60,
            refresh_token=refresh_value,
            user=user_to_out(user),
        ),
        meta=Meta(),
    )


@router.post("/otp/request")
async def request_otp(
    body: OTPRequestBody,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Envelope[dict]:
    mobile_hash = hash_value(body.mobile)
    allowed, retry_after = check_mobile_otp_limit(mobile_hash)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many OTP requests for this mobile",
            headers={"Retry-After": str(retry_after)},
        )

    try:
        await auth_service.request_otp(db, body.mobile)
    except Exception as exc:
        await write_auth_audit_committed(
            event_type="otp.request",
            success=False,
            mobile_hash=mobile_hash,
            ip=_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            detail={"error": "sms_send_failed"},
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to send OTP. Please try again shortly.",
        ) from exc

    await write_auth_audit(
        db,
        event_type="otp.request",
        success=True,
        mobile_hash=mobile_hash,
        ip=_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
        detail={"provider": settings.sms_provider if not settings.otp_mock_mode else "mock"},
    )
    return Envelope(
        data={
            "message": "OTP sent",
            "expires_in_seconds": settings.otp_ttl_seconds,
            "retry_after_seconds": 60,
            **({"mock_otp": settings.otp_mock_code} if settings.otp_mock_mode else {}),
        },
        meta=Meta(),
    )


@router.post("/otp/verify")
async def verify_otp(
    body: OTPVerifyBody,
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Envelope[TokenResponse]:
    mobile_hash = hash_value(body.mobile)
    try:
        user = await auth_service.verify_otp(db, body.mobile, body.otp)
    except ValueError as exc:
        await write_auth_audit_committed(
            event_type="otp.verify.fail",
            success=False,
            mobile_hash=mobile_hash,
            ip=_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            detail={"reason": str(exc)},
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    await write_auth_audit(
        db,
        event_type="otp.verify.success",
        success=True,
        actor_user_id=user.id,
        mobile_hash=mobile_hash,
        ip=_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return await _token_envelope(db, user, response)


@router.post("/google")
async def google_auth(
    body: GoogleAuthRequest,
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Envelope[TokenResponse]:
    if not settings.google_auth_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Google sign-in is disabled")

    google_id: str | None = None
    email = body.email
    name = body.name or "Google User"
    avatar_url = body.avatar_url

    if not settings.google_oauth_mock_mode:
        if not settings.google_client_id:
            raise HTTPException(status_code=503, detail="Google sign-in is not configured")
        try:
            from google.auth.transport import requests as google_requests
            from google.oauth2 import id_token

            info = id_token.verify_oauth2_token(
                body.id_token,
                google_requests.Request(),
                settings.google_client_id,
            )
            google_id = info["sub"]
            email = info.get("email")
            name = info.get("name") or "Google User"
            avatar_url = info.get("picture")
        except Exception as exc:
            await write_auth_audit_committed(
                event_type="google.login",
                success=False,
                ip=_client_ip(request),
                user_agent=request.headers.get("User-Agent"),
                detail={"error": "invalid_id_token"},
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google ID token",
            ) from exc
    else:
        # Dev / mock mode — accept client-supplied identity
        google_id = body.google_id or f"mock-{body.id_token[:32]}"
        if body.id_token.startswith("mock") and not email:
            email = "dev.user@railvoice.local"
            name = name or "Dev Google User"

    if not google_id:
        raise HTTPException(status_code=400, detail="google_id required")

    user = await auth_service.upsert_google_user(
        db,
        google_id=google_id,
        email=email,
        name=name,
        avatar_url=avatar_url,
    )
    await write_auth_audit(
        db,
        event_type="google.login",
        success=True,
        actor_user_id=user.id,
        ip=_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
        detail={"mock": settings.google_oauth_mock_mode},
    )
    return await _token_envelope(db, user, response)


@router.post("/refresh")
async def refresh_access_token(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    body: RefreshRequest = RefreshRequest(),
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> Envelope[TokenResponse]:
    token_value = body.refresh_token or refresh_token
    if not token_value:
        raise HTTPException(status_code=401, detail="Refresh token required")
    try:
        user, access_token, new_refresh = await auth_service.rotate_refresh_token(db, token_value)
    except ValueError as exc:
        event = "token.refresh.reuse" if "reuse" in str(exc).lower() else "token.refresh"
        await write_auth_audit_committed(
            event_type=event,
            success=False,
            ip=_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            detail={"reason": str(exc)},
        )
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    await write_auth_audit(
        db,
        event_type="token.refresh",
        success=True,
        actor_user_id=user.id,
        ip=_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )

    user_result = await db.execute(
        select(User)
        .options(selectinload(User.roles).selectinload(UserRole.role))
        .where(User.id == user.id)
    )
    user = user_result.scalar_one()
    _set_refresh_cookie(response, new_refresh)
    return Envelope(
        data=TokenResponse(
            access_token=access_token,
            expires_in=settings.access_token_expire_minutes * 60,
            refresh_token=new_refresh,
            user=user_to_out(user),
        ),
        meta=Meta(),
    )


@router.post("/anonymous")
async def create_anonymous_session(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Envelope[AnonymousSessionOut]:
    user = await auth_service.create_anonymous_user(db)
    return Envelope(
        data=AnonymousSessionOut(
            anonymous_session_id=user.anonymous_session_id,
            limits={
                "issues_per_24h": settings.anonymous_daily_issue_limit,
                "issues_remaining": settings.anonymous_daily_issue_limit,
            },
        ),
        meta=Meta(),
    )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
    )
    for token in result.scalars().all():
        token.revoked_at = datetime.now(timezone.utc)
    await write_auth_audit(
        db,
        event_type="logout",
        success=True,
        actor_user_id=user.id,
        ip=_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    response.delete_cookie("refresh_token", path="/api/v1/auth")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
