"""Production startup preparation (Logistic Regression only).

Trains ONLY the Logistic Regression model when the encrypted production
model (``logistic_regression.enc``) is missing or invalid, then exits so the
container can start FastAPI/Uvicorn immediately.

Decision Tree and Random Forest are never trained, generated, loaded or
compared by this module — this is the only training entry point used in the
production Docker startup path.
"""

import io
import json
import sys
from datetime import datetime, timezone

import joblib

from sklearn.model_selection import train_test_split

from app.core.config import get_settings
from app.core.encryption import decrypt_bytes
from app.ml.model_manager import MODEL_KEY
from app.ml.preprocess import ALL_COLUMNS, TARGET_COLUMN
from app.ml.train import (
    MODEL_CONFIGS,
    RANDOM_STATE,
    TEST_SIZE,
    audit_dataset,
    load_dataset,
    train_single_model,
)


def _model_is_ready() -> bool:
    """True when the encrypted Logistic Regression model can be used as-is."""
    settings = get_settings()
    enc_path = settings.ENCRYPTED_MODELS_DIR / f"{MODEL_KEY}.enc"
    if not enc_path.exists():
        return False
    try:
        plaintext = decrypt_bytes(enc_path.read_bytes())
        joblib.load(io.BytesIO(plaintext))
    except Exception as exc:
        print(f"Encrypted model {enc_path.name} exists but is invalid "
              f"({exc}) — will retrain.")
        return False
    registry_path = settings.ENCRYPTED_MODELS_DIR / "registry.json"
    if not registry_path.exists() or not settings.METRICS_PATH.exists():
        return False
    try:
        registry = json.loads(registry_path.read_text())
    except Exception:
        return False
    return any(e.get("key") == MODEL_KEY for e in registry.get("models", []))


def ensure_production_model() -> dict:
    settings = get_settings()
    if _model_is_ready():
        print("Logistic Regression encrypted model already present — "
              "skipping training.")
        return {}

    config = next(c for c in MODEL_CONFIGS if c["key"] == MODEL_KEY)

    df, raw_rows = load_dataset(settings.DATASET_PATH)
    audit = audit_dataset(df, raw_rows)

    X = df[ALL_COLUMNS]
    y = df[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y,
    )
    print(f"Train: {len(X_train)} rows, Test: {len(X_test)} rows")

    result = train_single_model(config, X_train, y_train, X_test, y_test)

    metrics_doc = {
        "version": settings.MODEL_VERSION,
        "training_date": datetime.now(timezone.utc).isoformat(),
        "dataset": {
            "source": settings.DATASET_PATH.name,
            "rows_after_cleanup": int(len(df)),
            "train_rows": int(len(X_train)),
            "test_rows": int(len(X_test)),
            "target_distribution": df[TARGET_COLUMN].value_counts().to_dict(),
            "audit": audit,
        },
        "cv": {MODEL_KEY: result["cv_report"]},
        "models": {MODEL_KEY: result["metrics"]},
        "feature_names": result["feature_names"],
    }
    settings.METRICS_PATH.write_text(json.dumps(metrics_doc, indent=2))
    settings.ENCRYPTED_MODELS_DIR.joinpath("registry.json").write_text(
        json.dumps({"version": settings.MODEL_VERSION,
                    "models": [result["saved_entry"]]}, indent=2))
    print(f"Logistic Regression production model ready -> {MODEL_KEY}.enc")
    return metrics_doc


if __name__ == "__main__":
    print("Preparing production model (Logistic Regression only)...")
    try:
        ensure_production_model()
    except Exception as exc:
        print(f"Model preparation failed: {exc}", file=sys.stderr)
        sys.exit(1)
