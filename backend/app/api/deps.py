from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyCookie, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.database import get_db
from app.db.models import User

_cookie_scheme = APIKeyCookie(name="access_token", auto_error=False)
_bearer_scheme = HTTPBearer(auto_error=False)


def _extract_token(
    request: Request,
    cookie_token: str | None = Depends(_cookie_scheme),
    bearer: object | None = Depends(_bearer_scheme),
) -> str:
    if cookie_token:
        return cookie_token
    if bearer is not None and getattr(bearer, "credentials", None):
        return bearer.credentials
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated. Please log in.",
    )


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    token: Annotated[str, Depends(_extract_token)],
) -> User:
    try:
        payload = decode_token(token, "access")
        user_id = int(payload["sub"])
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid. Please log in again.",
        ) from None
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is not active.",
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
