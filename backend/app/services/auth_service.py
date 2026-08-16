import hashlib
import datetime as dt
from typing import Any

import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.models import RefreshToken, User
from app.utils.hashing import hash_ip
from app.utils.validators import validate_email, validate_name, validate_password

REFRESH_COOKIE = "refresh_token"
ACCESS_COOKIE = "access_token"


def register(db: Session, name: str, email: str, password: str,
             confirm_password: str) -> tuple[User | None, str | None]:
    name = name.strip()
    email = email.strip().lower()
    for validator, value in ((validate_name, name), (validate_email, email),
                             (validate_password, password)):
        error = validator(value)
        if error:
            return None, error
    if password != confirm_password:
        return None, "Passwords do not match."
    if db.scalar(select(User).where(User.email == email)):
        return None, "An account with this email already exists."
    user = User(name=name, email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, None


def authenticate(db: Session, email: str, password: str) -> User | None:
    email = email.strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def issue_tokens(db: Session, user: User, ip: str | None = None) -> tuple[str, str]:
    settings = get_settings()
    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=_hash_token(refresh),
        expires_at=dt.datetime.now(dt.timezone.utc)
        + dt.timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        ip_hash=hash_ip(ip) if ip else None,
    ))
    db.commit()
    return access, refresh


def rotate_refresh_token(db: Session, refresh_token: str) -> tuple[str, str] | None:
    try:
        payload = decode_token(refresh_token, "refresh")
        user_id = int(payload["sub"])
    except jwt.PyJWTError:
        return None

    stored = db.scalar(select(RefreshToken).where(
        RefreshToken.token_hash == _hash_token(refresh_token)))
    if stored is None or stored.revoked_at is not None:
        return None
    expires_at = stored.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=dt.timezone.utc)
    if expires_at < dt.datetime.now(dt.timezone.utc):
        return None

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        return None

    stored.revoked_at = dt.datetime.now(dt.timezone.utc)
    access, refresh = issue_tokens(db, user, ip=stored.ip_hash)
    return access, refresh


def revoke_refresh_token(db: Session, refresh_token: str | None) -> None:
    if not refresh_token:
        return
    stored = db.scalar(select(RefreshToken).where(
        RefreshToken.token_hash == _hash_token(refresh_token)))
    if stored and stored.revoked_at is None:
        stored.revoked_at = dt.datetime.now(dt.timezone.utc)
        db.commit()


def revoke_all_sessions(db: Session, user: User) -> None:
    for token in user.refresh_tokens:
        if token.revoked_at is None:
            token.revoked_at = dt.datetime.now(dt.timezone.utc)
    db.commit()


def active_sessions(db: Session, user: User) -> list[dict[str, Any]]:
    sessions = []
    for token in user.refresh_tokens:
        sessions.append({
            "id": token.id,
            "created_at": token.created_at,
            "expires_at": token.expires_at,
            "revoked": token.revoked_at is not None,
            "ip_hash": token.ip_hash,
        })
    return sessions


def revoke_session(db: Session, user: User, session_id: int) -> bool:
    token = db.get(RefreshToken, session_id)
    if token is None or token.user_id != user.id:
        return False
    if token.revoked_at is None:
        token.revoked_at = dt.datetime.now(dt.timezone.utc)
        db.commit()
    return True


def change_password(db: Session, user: User, old_password: str,
                    new_password: str) -> str | None:
    if not verify_password(old_password, user.password_hash):
        return "Current password is incorrect."
    error = validate_password(new_password)
    if error:
        return error
    user.password_hash = hash_password(new_password)
    revoke_all_sessions(db, user)
    db.commit()
    return None


def set_auth_cookies(response, access: str, refresh: str) -> None:
    settings = get_settings()
    for name, token, max_age in (
        (ACCESS_COOKIE, access, settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60),
        (REFRESH_COOKIE, refresh, settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600),
    ):
        response.set_cookie(
            key=name,
            value=token,
            max_age=max_age,
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite="lax",
            path="/",
        )


def clear_auth_cookies(response) -> None:
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/")
