import os
import shutil
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
TEST_DB = BACKEND_DIR / "test_heartguard.db"

os.environ["APP_ENV"] = "development"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"
os.environ["RATE_LIMIT_LOGIN"] = "1000/minute"
os.environ["RATE_LIMIT_REGISTER"] = "1000/minute"
os.environ["RATE_LIMIT_PREDICTION"] = "1000/minute"
os.environ["COOKIE_SECURE"] = "false"

if not (BACKEND_DIR / ".env").exists():
    os.environ["ENCRYPTION_KEY"] = "dGVzdC1rZXktZm9yLXRlc3RzLW9ubHktMzItYnl0ZXMhIQ=="
    os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-not-for-production"
    os.environ["AUDIT_SALT"] = "test-audit-salt"


@pytest.fixture(autouse=True, scope="session")
def _clean_test_db():
    if TEST_DB.exists():
        try:
            TEST_DB.unlink()
        except PermissionError:
            pass
    yield
    from app.db.database import engine

    engine.dispose()
    if TEST_DB.exists():
        try:
            TEST_DB.unlink()
        except PermissionError:
            pass


@pytest.fixture(autouse=True)
def _fresh_cookie_jar(client):
    client.cookies.clear()
    yield
    client.cookies.clear()


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def models_ready():
    from app.ml.model_manager import ModelManager

    manager = ModelManager.get_instance()
    if not manager.is_loaded:
        try:
            manager.load()
        except Exception as exc:
            pytest.skip(f"Models not available ({exc}). Run `python -m app.ml.train` first.")


@pytest.fixture()
def auth_headers(client):
    import uuid

    email = f"test{uuid.uuid4().hex[:10]}@example.com"
    password = "StrongPass1"
    response = client.post("/api/auth/register", json={
        "name": "Test User",
        "email": email,
        "password": password,
        "confirm_password": password,
    })
    assert response.status_code == 201, response.text
    return {"cookies": response.cookies}


VALID_PAYLOAD = {
    "age": 58, "sex": "Male", "cp": "Asymptomatic",
    "trestbps": 145, "chol": 233, "fbs": "Yes",
    "restecg": "Normal", "thalach": 150, "exang": "No",
    "oldpeak": 2.3, "slope": "Flat", "ca": "0 vessels", "thal": "Normal",
}


@pytest.fixture()
def valid_payload():
    return dict(VALID_PAYLOAD)


@pytest.fixture()
def created_prediction(client, auth_headers, valid_payload):
    response = client.post("/api/predictions", json=valid_payload,
                           cookies=auth_headers["cookies"])
    assert response.status_code == 201, response.text
    return response.json()
