import os
import sys

os.environ.setdefault("APP_ENV", "development")

from fastapi.testclient import TestClient

from app.main import app

VALID_PAYLOAD = {
    "age": 58, "sex": "Male", "cp": "Asymptomatic",
    "trestbps": 145, "chol": 233, "fbs": "Yes",
    "restecg": "Normal", "thalach": 150, "exang": "No",
    "oldpeak": 2.3, "slope": "Flat", "ca": "0 vessels", "thal": "Normal",
}

client = TestClient(app)
client.raise_server_exceptions = False
results = []

from app.ml.model_manager import ModelManager

ModelManager.get_instance().load()


def check(name, condition):
    results.append((name, condition))
    print(("PASS " if condition else "FAIL ") + name)


r = client.get("/api/health")
check("health endpoint", r.status_code == 200 and r.json()["status"] == "healthy")

import uuid
email = f"smoke{uuid.uuid4().hex[:8]}@example.com"
r = client.post("/api/auth/register", json={
    "name": "Smoke Tester", "email": email,
    "password": "StrongPass1", "confirm_password": "StrongPass1",
})
check("register", r.status_code == 201 and "access_token" in r.cookies)
print("   cookies:", sorted(r.cookies.keys()))

r = client.get("/api/auth/me")
check("me (authenticated)", r.status_code == 200 and r.json()["email"] == email)

r = client.post("/api/predictions", json=VALID_PAYLOAD)
check("prediction created", r.status_code == 201)
data = r.json()
print("   result:", data.get("classification"),
      data.get("model", {}).get("model_name"),
      data.get("risk_score_percent"))
check("single unified prediction (no per-model dicts)", "models" not in data
      and data.get("prediction") in (0, 1))
check("logistic regression model exposed with real metrics", "model" in data
      and data["model"]["model_key"] == "logistic_regression"
      and data["model"]["metrics"]["roc_auc"] > 0)
check("probability present", 0.0 <= data.get("probability", -1) <= 1.0)

r = client.get("/api/predictions")
check("history list", r.status_code == 200 and r.json()["total"] >= 1)

pid = data["prediction_id"]
r = client.get(f"/api/predictions/{pid}")
check("prediction detail", r.status_code == 200 and
      r.json()["input_features"]["sex"] == "Male")

bad = dict(VALID_PAYLOAD, age=999)
r = client.post("/api/predictions", json=bad)
check("invalid age rejected (422)", r.status_code == 422)

r = client.get("/api/models/insights")
check("model insights (single model)", r.status_code == 200 and
      r.json()["model"]["key"] == "logistic_regression")

r = client.get("/api/models/features")
check("feature definitions", r.status_code == 200 and len(r.json()) == 13)

email2 = f"smoke2{uuid.uuid4().hex[:8]}@example.com"
r = client.post("/api/auth/register", json={
    "name": "Smoke Tester 2", "email": email2,
    "password": "StrongPass1", "confirm_password": "StrongPass1",
})
client2 = TestClient(app)
r2 = client2.post("/api/auth/login", json={"email": email2,
                                           "password": "StrongPass1"})
r3 = client2.get(f"/api/predictions/{pid}")
check("cross-user access blocked (404)", r3.status_code == 404)

anon = TestClient(app)
r = anon.get("/api/predictions")
check("unauthenticated blocked (401)", r.status_code == 401)

r = client.post("/api/auth/logout")
check("logout", r.status_code == 200)
r = client.get("/api/auth/me")
check("me after logout (401)", r.status_code == 401)

failed = [n for n, ok in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
