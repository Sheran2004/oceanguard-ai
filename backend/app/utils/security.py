"""Authentication & password hashing helpers."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.utils.config import get_settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    # bcrypt has a 72-byte cap; we pre-truncate to be safe.
    safe = plain.encode("utf-8")[:72].decode("utf-8", errors="ignore")
    return pwd_context.hash(safe)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        safe = plain.encode("utf-8")[:72].decode("utf-8", errors="ignore")
        return pwd_context.verify(safe, hashed)
    except Exception:
        return False


def create_access_token(subject: str, *, expires_minutes: Optional[int] = None,
                        extra: Optional[dict] = None) -> str:
    settings = get_settings()
    exp = datetime.now() + timedelta(
        minutes=expires_minutes if expires_minutes is not None else settings.access_token_expire_minutes
    )
    payload = {"sub": subject, "exp": exp, "iat": datetime.now()}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError(f"Invalid token: {exc}") from exc