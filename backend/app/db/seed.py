import json
import random

from sqlalchemy import select

from app.core.config import get_settings
from app.core.encryption import encrypt_str
from app.core.security import hash_password
from app.db.database import SessionLocal, init_db
from app.db.models import Prediction, User
from app.ml.predict import run_prediction
from app.ml.preprocess import map_form_to_dataset

DEMO_USER = {"name": "Demo Student", "email": "demo@heartguard.local",
             "password": "DemoPass123"}

FEATURE_RANGES = {
    "age": (29, 77), "sex": [0, 1], "cp": [0, 1, 2, 3],
    "trestbps": (94, 200), "chol": (126, 564), "fbs": [0, 1],
    "restecg": [0, 1, 2], "thalach": (71, 202), "exang": [0, 1],
    "oldpeak": (0.0, 6.2), "slope": [0, 1, 2], "ca": [0, 1, 2, 3, 4],
    "thal": [0, 1, 2, 3],
}



def _random_features() -> dict:
    features = {}
    for key, spec in FEATURE_RANGES.items():
        if isinstance(spec, list):
            features[key] = random.choice(spec)
        else:
            lo, hi = spec
            value = random.uniform(lo, hi)
            features[key] = round(value, 1) if key == "oldpeak" else int(value)
    return features


def seed(num_predictions: int = 12) -> None:
    settings = get_settings()
    init_db()
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == DEMO_USER["email"]))
        if user is None:
            user = User(name=DEMO_USER["name"], email=DEMO_USER["email"],
                        password_hash=hash_password(DEMO_USER["password"]))
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"Created demo user: {DEMO_USER['email']} "
                  f"(password: {DEMO_USER['password']})")
        else:
            print(f"Demo user already exists: {DEMO_USER['email']}")

        existing = db.scalar(
            select(Prediction).where(Prediction.user_id == user.id))
        if existing is not None:
            print("Demo predictions already exist — skipping.")
            return

        for _ in range(num_predictions):
            form = _random_features()
            features = map_form_to_dataset(form)
            raw = run_prediction(features)
            payload = {
                "prediction": raw["prediction"],
                "classification": raw["classification"],
                "label": raw["label"],
                "probability": raw["probability"],
                "risk_score_percent": raw["risk_score_percent"],
                "model": raw["model"],
            }
            db.add(Prediction(
                user_id=user.id,
                encrypted_input_data=encrypt_str(json.dumps(form)),
                encrypted_result=encrypt_str(json.dumps(payload)),
                model_version=settings.MODEL_VERSION,
                consensus=payload["label"],
                best_model=payload["model"]["model_key"],
                best_model_name=payload["model"]["model_name"],
                probability=payload["probability"],
            ))
        db.commit()
        print(f"Seeded {num_predictions} synthetic predictions for the demo user.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
