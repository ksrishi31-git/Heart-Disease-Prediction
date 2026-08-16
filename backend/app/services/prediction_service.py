import json

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.encryption import decrypt_str, encrypt_str
from app.db.models import Prediction, User
from app.ml.predict import run_prediction
from app.ml.preprocess import map_form_to_dataset


def _build_result_payload(raw_result: dict) -> dict:
    return {
        "prediction": raw_result["prediction"],
        "classification": raw_result["classification"],
        "label": raw_result["label"],
        "probability": raw_result["probability"],
        "risk_score_percent": raw_result["risk_score_percent"],
        "model": raw_result["model"],
    }


def create_prediction(db: Session, user: User, form_data: dict) -> dict:
    settings = get_settings()

    features = map_form_to_dataset(form_data)

    raw_result = run_prediction(features)
    payload = _build_result_payload(raw_result)

    record = Prediction(
        user_id=user.id,
        encrypted_input_data=encrypt_str(json.dumps(form_data)),
        encrypted_result=encrypt_str(json.dumps(payload)),
        model_version=settings.MODEL_VERSION,
        consensus=payload["label"],
        best_model=payload["model"]["model_key"],
        best_model_name=payload["model"]["model_name"],
        probability=payload["probability"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "prediction_id": record.uuid,
        "created_at": record.created_at,
        "model_version": record.model_version,
        **payload,
    }


def list_predictions(db: Session, user: User, limit: int = 20,
                     offset: int = 0) -> dict:
    total = db.scalar(select(func.count(Prediction.id)).where(
        Prediction.user_id == user.id)) or 0
    rows = db.scalars(
        select(Prediction)
        .where(Prediction.user_id == user.id)
        .order_by(Prediction.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    items = [
        {
            "prediction_id": row.uuid,
            "created_at": row.created_at,
            "consensus": row.consensus,
            "best_model": row.best_model,
            "best_model_name": row.best_model_name,
            "probability": row.probability,
            "model_version": row.model_version,
        }
        for row in rows
    ]
    return {"total": total, "items": items}


def get_prediction(db: Session, user: User, prediction_uuid: str) -> dict | None:
    row = db.scalar(select(Prediction).where(
        Prediction.uuid == prediction_uuid, Prediction.user_id == user.id))
    if row is None:
        return None
    payload = json.loads(decrypt_str(row.encrypted_result))
    input_features = json.loads(decrypt_str(row.encrypted_input_data))
    return {
        "prediction_id": row.uuid,
        "created_at": row.created_at,
        "model_version": row.model_version,
        "input_features": input_features,
        **payload,
    }


def delete_prediction(db: Session, user: User, prediction_uuid: str) -> bool:
    row = db.scalar(select(Prediction).where(
        Prediction.uuid == prediction_uuid, Prediction.user_id == user.id))
    if row is None:
        return False
    db.delete(row)
    db.commit()
    return True


def dashboard_stats(db: Session, user: User) -> dict:
    rows = db.scalars(select(Prediction).where(
        Prediction.user_id == user.id).order_by(Prediction.created_at.desc())).all()
    total = len(rows)
    positive = sum(1 for r in rows if r.consensus == "Positive")
    negative = total - positive
    latest = rows[0] if rows else None
    return {
        "total_predictions": total,
        "positive": positive,
        "negative": negative,
        "latest": {
            "prediction_id": latest.uuid,
            "consensus": latest.consensus,
            "best_model_name": latest.best_model_name,
            "probability": latest.probability,
            "created_at": latest.created_at,
        } if latest else None,
    }
