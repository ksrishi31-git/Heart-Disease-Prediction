from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ModelMetadata
from app.ml.model_manager import ModelManager


def sync_model_metadata(db: Session) -> None:
    manager = ModelManager.get_instance()
    metrics = manager.metrics()
    if not metrics:
        return
    registry = getattr(manager, "_registry", None) or {}
    paths = {e["key"]: e["path"] for e in registry.get("models", [])}

    for key, values in metrics.get("models", {}).items():
        existing = db.scalar(select(ModelMetadata).where(
            ModelMetadata.model_name == key,
            ModelMetadata.model_version == metrics["version"]))
        training_date = datetime.fromisoformat(metrics["training_date"])
        data = {
            "model_name": key,
            "model_version": metrics["version"],
            "algorithm": _algorithm_for(key),
            "training_date": training_date,
            "accuracy": values["accuracy"],
            "precision": values["precision"],
            "recall": values["recall"],
            "f1_score": values["f1"],
            "roc_auc": values["roc_auc"],
            "encrypted_model_path": paths.get(key, f"{key}.enc"),
        }
        if existing:
            for field, value in data.items():
                setattr(existing, field, value)
        else:
            db.add(ModelMetadata(**data))
    db.commit()


def _algorithm_for(key: str) -> str:
    return {
        "logistic_regression": "LogisticRegression",
        "decision_tree": "DecisionTreeClassifier",
        "random_forest": "RandomForestClassifier",
    }.get(key, key)


def insights() -> dict:
    return ModelManager.get_instance().insights()


def model_metrics(key: str) -> dict:
    return ModelManager.get_instance().model_metrics(key)


def feature_definitions() -> list[dict]:
    return ModelManager.get_instance().feature_definitions()
