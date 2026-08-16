from fastapi import APIRouter, HTTPException, Request, status

from app.api.deps import CurrentUser, DbSession, get_client_ip
from app.core.logging_config import get_logger
from app.db.schemas import MessageOut, PasswordChange, SessionOut
from app.services import auth_service as auth
from app.services.audit_service import log_action

logger = get_logger("app.api.users")
router = APIRouter(prefix="/users", tags=["users"])


@router.post("/change-password", response_model=MessageOut)
def change_password(payload: PasswordChange, request: Request,
                    db: DbSession, current_user: CurrentUser):
    error = auth.change_password(db, current_user, payload.old_password,
                                 payload.new_password)
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    log_action("password_changed", user_id=current_user.id,
               ip=get_client_ip(request))
    logger.info("Password changed", extra={"user_id": current_user.id,
                                           "action": "password_changed"})
    return MessageOut(message="Password updated. Other sessions have been signed out.")


@router.get("/sessions", response_model=list[SessionOut])
def list_sessions(db: DbSession, current_user: CurrentUser):
    return auth.active_sessions(db, current_user)


@router.delete("/sessions/{session_id}", response_model=MessageOut)
def revoke_session(session_id: int, db: DbSession, current_user: CurrentUser):
    if not auth.revoke_session(db, current_user, session_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Session not found.")
    return MessageOut(message="Session revoked.")


@router.delete("/me", response_model=MessageOut)
def delete_account(request: Request, db: DbSession, current_user: CurrentUser):
    user_id = current_user.id
    db.delete(current_user)
    db.commit()
    log_action("account_deleted", user_id=user_id, ip=get_client_ip(request))
    logger.info("Account deleted", extra={"user_id": user_id,
                                          "action": "account_deleted"})
    return MessageOut(message="Your account and all associated data were deleted.")
