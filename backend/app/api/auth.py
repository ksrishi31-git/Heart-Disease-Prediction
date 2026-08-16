from fastapi import APIRouter, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, DbSession, get_client_ip
from app.api.rate_limit import limiter
from app.core.config import get_settings
from app.core.logging_config import get_logger
from app.core.security import decode_token
from app.db.models import User
from app.db.schemas import MessageOut, TokenResponse, UserLogin, UserOut, UserRegister
from app.services import auth_service as auth
from app.services.audit_service import log_action

logger = get_logger("app.api.auth")
router = APIRouter(prefix="/auth", tags=["auth"])

settings = get_settings()


def _issue_and_set_cookies(response: Response, db: Session, user,
                           ip: str) -> TokenResponse:
    access, refresh = auth.issue_tokens(db, user, ip=ip)
    auth.set_auth_cookies(response, access, refresh)
    return TokenResponse(
        access_token_expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserOut.model_validate(user),
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_REGISTER)
def register(payload: UserRegister, request: Request, response: Response,
             db: DbSession):
    ip = get_client_ip(request)
    user, error = auth.register(db, payload.name, payload.email,
                                payload.password, payload.confirm_password)
    if error:
        log_action("register_failed", ip=ip, success=False)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    log_action("register", user_id=user.id, ip=ip)
    logger.info("User registered", extra={"user_id": user.id, "action": "register"})
    return _issue_and_set_cookies(response, db, user, ip)


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
def login(payload: UserLogin, request: Request, response: Response, db: DbSession):
    ip = get_client_ip(request)
    user = auth.authenticate(db, payload.email, payload.password)
    if user is None:
        log_action("login_failed", ip=ip, success=False)
        logger.info("Login failed", extra={"action": "login_failed"})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect email or password.")
    log_action("login", user_id=user.id, ip=ip)
    logger.info("User logged in", extra={"user_id": user.id, "action": "login"})
    return _issue_and_set_cookies(response, db, user, ip)


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: Request, response: Response, db: DbSession):
    refresh_token = request.cookies.get(auth.REFRESH_COOKIE)
    pair = auth.rotate_refresh_token(db, refresh_token) if refresh_token else None
    if pair is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Session expired. Please log in again.")
    access, new_refresh = pair
    auth.set_auth_cookies(response, access, new_refresh)
    payload = decode_token(access, "access")
    user_id = int(payload["sub"])
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Account no longer exists.")
    log_action("token_refresh", user_id=user_id, ip=get_client_ip(request))
    return TokenResponse(
        access_token_expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserOut.model_validate(user),
    )


@router.post("/logout", response_model=MessageOut)
def logout(request: Request, response: Response, db: DbSession):
    refresh_token = request.cookies.get(auth.REFRESH_COOKIE)
    auth.revoke_refresh_token(db, refresh_token)
    auth.clear_auth_cookies(response)
    user_id = None
    try:
        access = request.cookies.get(auth.ACCESS_COOKIE)
        if access:
            user_id = int(auth.decode_token(access, "access")["sub"])
    except Exception:
        pass
    log_action("logout", user_id=user_id, ip=get_client_ip(request))
    return MessageOut(message="Logged out successfully.")


@router.get("/me", response_model=UserOut)
def me(current_user: CurrentUser):
    return current_user
