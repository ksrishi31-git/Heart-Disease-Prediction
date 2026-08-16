from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.api.deps import DbSession
from app.core.config import get_settings
from app.db.schemas import HealthOut
from app.ml.model_manager import ModelManager

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthOut)
def health():
    return HealthOut(
        status="healthy",
        database="not_checked",
        models="not_checked",
        version=get_settings().MODEL_VERSION,
    )


@router.get("/ready", response_model=HealthOut)
def readiness(db: DbSession):
    try:
        db.execute(text("SELECT 1"))
        database = "ok"
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable.") from None

    manager = ModelManager.get_instance()
    if not manager.is_loaded:
        try:
            manager.load()
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Models not ready: {exc}",
            ) from None
    return HealthOut(status="ready", database=database, models="ok",
                     version=get_settings().MODEL_VERSION)
