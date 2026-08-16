from fastapi import APIRouter, HTTPException

from app.db.schemas import (
    FeatureDefinitionOut,
    ModelInsightsOut,
    ModelMetricsOut,
)
from app.ml.model_manager import MODEL_KEY, ModelNotReadyError
from app.services import model_service

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/features", response_model=list[FeatureDefinitionOut])
def feature_definitions():
    return model_service.feature_definitions()


@router.get("/insights", response_model=ModelInsightsOut)
def insights():
    try:
        return model_service.insights()
    except ModelNotReadyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None


@router.get("", response_model=ModelMetricsOut)
def get_model():
    try:
        return model_service.model_metrics(MODEL_KEY)
    except ModelNotReadyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None


@router.get("/{model_name}/metrics", response_model=ModelMetricsOut)
def model_metrics(model_name: str):
    try:
        return model_service.model_metrics(model_name)
    except ModelNotReadyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
