"""Authentication endpoints: register, login, current-user info."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from sqlalchemy.orm import Session

# Allow special-use / private TLDs (e.g. "oceanguard.local") for the demo.
from email_validator import validate_email as _ev_validate, EmailNotValidError

def _loose_email(value: str) -> str:
    """Permissive email validator — accepts .local / .test / .example domains."""
    try:
        info = _ev_validate(value, check_deliverability=False, test_environment=True)
        return info.normalized
    except EmailNotValidError:
        # Last-resort: require at least an "@" with non-empty parts.
        if "@" in value and len(value.split("@", 1)) == 2:
            local, _, domain = value.partition("@")
            if local and domain and "." in domain:
                return value
        raise ValueError(f"Invalid email address: {value}")

from app.models.database import get_db
from app.models.orm import User
from app.utils.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


router = APIRouter(prefix="/api/auth", tags=["auth"])

# tokenUrl is used by Swagger's OAuth helper. We keep the same path.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


# ===== Schemas =====

class RegisterIn(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=80,
        pattern=r"^[a-zA-Z0-9_-]+$",
    )
    password: str = Field(..., min_length=6, max_length=72)
    email: Optional[str] = Field(default=None, max_length=200)
    full_name: Optional[str] = Field(default=None, max_length=160)

    @field_validator("email")
    @classmethod
    def _validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        return _loose_email(v)


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserOut"


class UserOut(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PasswordChangeIn(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6, max_length=72)


# ===== Dependencies =====

def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token payload.")
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive.")
    return user


def require_role(*roles: str):
    """Dependency factory that allows only the listed roles."""
    def _check(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail=f"Role '{user.role}' is not allowed for this action.")
        return user
    return _check


# ===== Endpoints =====
@router.post("/register", response_model=UserOut, status_code=201)
def register(payload: RegisterIn, db: Session = Depends(get_db)) -> User:
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=409, detail="Username already exists.")

    if payload.email and db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email already registered.")

    # Public registration must never grant privileged roles.
    user = User(
        username=payload.username,
        email=payload.email,
        full_name=payload.full_name,
        role="operator",
        hashed_password=hash_password(payload.password),
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)) -> TokenOut:
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is inactive.")

    user.last_login_at = datetime.now()
    db.commit()
    db.refresh(user)

    from app.utils.config import get_settings
    settings = get_settings()
    token = create_access_token(user.username, extra={"role": user.role})
    return TokenOut(
        access_token=token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserOut.model_validate(user),
    )


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)


@router.post("/change-password")
def change_password(
    payload: PasswordChangeIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if not verify_password(payload.current_password, user.hashed_password or ""):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"detail": "Password updated successfully."}


@router.post("/logout")
def logout(user: User = Depends(get_current_user)) -> dict:
    # Stateless JWT — client should drop the token. Logged here for traceability.
    return {"detail": "Logged out. Please discard the bearer token client-side."}


TokenOut.model_rebuild()