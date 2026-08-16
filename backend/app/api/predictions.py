from fastapi import APIRouter, HTTPException, Query, Request, status

from app.api.deps import CurrentUser, DbSession, get_client_ip
from app.api.rate_limit import limiter, user_key
from app.core.config import get_settings
from app.core.logging_config import get_logger
from app.db.schemas import (
    MessageOut,
    PredictionDetailOut,
    PredictionListOut,
    PredictionRequest,
    PredictionResultOut,
)
from app.ml.model_manager import ModelNotReadyError
from app.services import prediction_service as predictions
from app.services.audit_service import log_action

logger = get_logger("app.api.predictions")
router = APIRouter(prefix="/predictions", tags=["predictions"])

settings = get_settings()


@router.get("/stats")
def dashboard_stats(db: DbSession, current_user: CurrentUser):
    return predictions.dashboard_stats(db, current_user)


@router.post("", response_model=PredictionResultOut, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_PREDICTION, key_func=user_key)
def create_prediction(payload: PredictionRequest, request: Request,
                      db: DbSession, current_user: CurrentUser):
    try:
        result = predictions.create_prediction(db, current_user,
                                               payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=str(exc)) from None
    except ModelNotReadyError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail=str(exc)) from None

    log_action("prediction_created", user_id=current_user.id,
               ip=get_client_ip(request))
    logger.info("Prediction created", extra={
        "user_id": current_user.id, "action": "prediction_created"})
    return PredictionResultOut(**result)


@router.get("", response_model=PredictionListOut)
def list_predictions(
    db: DbSession, current_user: CurrentUser,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    return predictions.list_predictions(db, current_user, limit=limit, offset=offset)


@router.get("/{prediction_id}", response_model=PredictionDetailOut)
def get_prediction(prediction_id: str, db: DbSession, current_user: CurrentUser):
    detail = predictions.get_prediction(db, current_user, prediction_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Prediction not found.")
    return detail


@router.delete("/{prediction_id}", response_model=MessageOut)
def delete_prediction(prediction_id: str, db: DbSession,
                      current_user: CurrentUser):
    if not predictions.delete_prediction(db, current_user, prediction_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Prediction not found.")
    log_action("prediction_deleted", user_id=current_user.id)
    return MessageOut(message="Prediction deleted.")
