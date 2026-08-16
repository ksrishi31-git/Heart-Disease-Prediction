import io
import json
import logging
from pathlib import Path

import joblib
import pandas as pd

from app.core.config import get_settings
from app.core.encryption import decrypt_bytes
from app.ml.preprocess import ALL_COLUMNS, FEATURE_DEFINITIONS

logger = logging.getLogger("app.ml.model_manager")

MODEL_KEY = "logistic_regression"
MODEL_NAME = "Logistic Regression"


class ModelNotReadyError(RuntimeError):
    pass


class ModelManager:
    _instance: "ModelManager | None" = None

    def __init__(self) -> None:
        self._pipeline: object | None = None
        self._metrics: dict | None = None
        self._registry: dict | None = None
        self._loaded = False

    @classmethod
    def get_instance(cls) -> "ModelManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def load(self) -> None:
        settings = get_settings()
        registry_path = settings.ENCRYPTED_MODELS_DIR / "registry.json"
        if not registry_path.exists():
            raise ModelNotReadyError(
                "Models are not trained. Run `python -m app.ml.train` "
                "from the backend/ directory first."
            )

        self._registry = json.loads(registry_path.read_text())
        entry = next((e for e in self._registry.get("models", [])
                      if e.get("key") == MODEL_KEY), None)
        if entry is None:
            raise ModelNotReadyError(
                f"Encrypted model '{MODEL_KEY}' is missing from the registry."
            )
        enc_path = settings.ENCRYPTED_MODELS_DIR / entry["path"]
        if not enc_path.exists():
            raise ModelNotReadyError(
                f"Encrypted model file missing: {entry['path']}"
            )
        plaintext = decrypt_bytes(enc_path.read_bytes())
        self._pipeline = joblib.load(io.BytesIO(plaintext))
        logger.info("Model loaded", extra={"model": MODEL_KEY})

        if settings.METRICS_PATH.exists():
            self._metrics = json.loads(settings.METRICS_PATH.read_text())
        self._loaded = True
        logger.info("Model ready", extra={"model": MODEL_KEY})

    def predict_single(self, features: dict) -> tuple[float, int]:
        if not self._loaded:
            self.load()
        if self._pipeline is None:
            raise ModelNotReadyError(f"Model '{MODEL_KEY}' is not loaded.")
        row = pd.DataFrame([{col: features[col] for col in ALL_COLUMNS}])
        proba = float(self._pipeline.predict_proba(row)[0][1])
        return round(proba, 4), int(proba >= 0.5)

    def human_name(self) -> str:
        return MODEL_NAME

    def metrics(self) -> dict | None:
        return self._metrics

    def insights(self) -> dict:
        if not self._metrics:
            raise ModelNotReadyError(
                "Model evaluation metrics are not available yet. Run "
                "`python -m app.ml.train` first."
            )
        raw = self._metrics.get("models", {}).get(MODEL_KEY)
        if raw is None:
            raise ModelNotReadyError(
                f"Metrics for '{MODEL_KEY}' are missing from metrics.json. "
                "Run `python -m app.ml.train`."
            )
        cv = self._metrics.get("cv", {}).get(MODEL_KEY, {})
        cv_metrics = {
            "accuracy": cv.get("accuracy", {}).get("mean"),
            "precision": cv.get("precision", {}).get("mean"),
            "sensitivity": cv.get("recall", {}).get("mean"),
            "specificity": cv.get("specificity", {}).get("mean"),
            "f1": cv.get("f1", {}).get("mean"),
            "roc_auc": cv.get("roc_auc", {}).get("mean"),
        }
        cv_metrics = {k: v for k, v in cv_metrics.items() if v is not None}
        registry_entry = next(
            (e for e in (self._registry or {}).get("models", [])
             if e.get("key") == MODEL_KEY), {})
        return {
            "version": self._metrics.get("version"),
            "training_date": self._metrics.get("training_date"),
            "dataset": self._metrics.get("dataset"),
            "model": {
                "key": MODEL_KEY,
                "name": MODEL_NAME,
                "algorithm": registry_entry.get("algorithm")
                             or "LogisticRegression",
                "hyperparameters": raw.get("hyperparameters", {}),
            },
            "test_metrics": {
                "accuracy": raw["accuracy"],
                "precision": raw["precision"],
                "sensitivity": raw["recall"],
                "specificity": raw["specificity"],
                "f1": raw["f1"],
                "roc_auc": raw["roc_auc"],
            },
            "cv_metrics": cv_metrics,
            "confusion_matrix": raw["confusion_matrix"],
            "roc_curve": raw["roc_curve"],
            "feature_importance": raw.get(
                "feature_importance",
                {"type": "coefficients", "values": {}}),
            "feature_names": self._metrics.get("feature_names", []),
        }

    def model_metrics(self, key: str) -> dict:
        if key != MODEL_KEY:
            raise KeyError(f"Unknown model '{key}'")
        if not self._metrics:
            raise ModelNotReadyError(
                "Model evaluation metrics are not available yet. Run "
                "`python -m app.ml.train` first."
            )
        raw = self._metrics.get("models", {}).get(MODEL_KEY)
        if raw is None:
            raise ModelNotReadyError(
                f"Metrics for '{MODEL_KEY}' are missing from metrics.json."
            )
        return {
            "key": MODEL_KEY,
            "human_name": MODEL_NAME,
            **raw,
        }

    def feature_definitions(self) -> list[dict]:
        return [
            {
                "name": f.name,
                "kind": f.kind,
                "label": f.label,
                "unit": f.unit,
                "min": f.min,
                "max": f.max,
                "step": f.step,
                "options": [{"value": v, "label": l}
                            for v, l in f.options.items()],
                "helper": f.helper,
            }
            for f in FEATURE_DEFINITIONS
        ]
