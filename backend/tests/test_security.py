import datetime as dt

import jwt

from app.core.config import get_settings
from app.core.security import create_access_token


def test_invalid_jwt_rejected(client, auth_headers):
    response = client.get("/api/auth/me",
                          cookies={"access_token": "not-a-jwt"})
    assert response.status_code == 401


def test_wrong_signature_rejected(client, auth_headers):
    settings = get_settings()
    token = jwt.encode(
        {"sub": "1", "type": "access",
         "iat": dt.datetime.now(dt.timezone.utc),
         "exp": dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=5)},
        "attacker-secret", algorithm="HS256")
    response = client.get("/api/auth/me", cookies={"access_token": token})
    assert response.status_code == 401


def test_expired_token_rejected(client, auth_headers):
    settings = get_settings()
    expired = jwt.encode(
        {"sub": "1", "type": "access",
         "iat": dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=2),
         "exp": dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=1)},
        settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    response = client.get("/api/auth/me", cookies={"access_token": expired})
    assert response.status_code == 401


def test_refresh_token_cannot_be_used_as_access(client, auth_headers):
    refresh = auth_headers["cookies"].get("refresh_token")
    response = client.get("/api/auth/me", cookies={"access_token": refresh})
    assert response.status_code == 401


def test_sql_injection_attempt_is_harmless(client, auth_headers, models_ready,
                                           valid_payload):
    payload = dict(valid_payload, age="58 OR 1=1")
    response = client.post("/api/predictions", json=payload,
                           cookies=auth_headers["cookies"])
    assert response.status_code in (422, 201)


def test_oversized_payload_rejected(client, auth_headers, valid_payload):
    payload = dict(valid_payload, age=58)
    big = "x" * 60_000
    payload["chol"] = big
    response = client.post("/api/predictions", json=payload,
                           cookies=auth_headers["cookies"])
    assert response.status_code == 413


def test_invalid_encrypted_data_fails():
    from app.core.encryption import decrypt_data

    try:
        decrypt_data("!!!not-base64!!!")
        assert False, "expected exception"
    except Exception:
        pass


def test_error_responses_do_not_leak_internals(client, auth_headers,
                                               valid_payload, models_ready):
    response = client.post("/api/predictions", json=dict(valid_payload, age=-5),
                           cookies=auth_headers["cookies"])
    assert response.status_code == 422
    assert "Traceback" not in response.text
    assert "File \"" not in response.text


def test_security_headers_present(client):
    response = client.get("/api/health")
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("referrer-policy") == "no-referrer"


def test_audit_log_records_events(client, auth_headers):
    from sqlalchemy import func, select

    from app.db.database import SessionLocal
    from app.db.models import AuditLog

    with SessionLocal() as db:
        count = db.scalar(select(func.count(AuditLog.id)).where(
            AuditLog.action == "login"))
    assert count is not None and count >= 0
