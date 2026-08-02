from datetime import datetime, timedelta, timezone
from typing import Any
import hashlib
import secrets
import uuid

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


def hash_value(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def create_access_token(subject: str, extra: dict[str, Any] | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "exp": expire, "type": "access"}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token_value() -> str:
    return secrets.token_urlsafe(48)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])


def verify_access_token(token: str) -> dict[str, Any] | None:
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def _password_bytes(password: str) -> bytes:
    """Bcrypt accepts at most 72 bytes — truncate safely on the byte boundary."""
    raw = password.encode("utf-8")
    if len(raw) <= 72:
        return raw
    return raw[:72]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_password_bytes(password), bcrypt.gensalt()).decode("ascii")


def verify_password(plain: str, hashed: str | None) -> bool:
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(_password_bytes(plain), hashed.encode("ascii"))
    except Exception:
        return False


def generate_temporary_password(length: int = 12) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def new_uuid() -> str:
    return str(uuid.uuid4())
