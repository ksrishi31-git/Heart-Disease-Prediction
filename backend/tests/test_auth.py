import hashlib
import uuid

from sqlalchemy import select

from app.core.security import hash_password, verify_password
from app.db.database import SessionLocal
from app.db.models import RefreshToken


def test_password_hash_not_plaintext():
    hashed = hash_password("SuperSecret1")
    assert hashed != "SuperSecret1"
    assert verify_password("SuperSecret1", hashed)
    assert not verify_password("WrongPass1", hashed)


def test_password_hash_salted():
    a = hash_password("SuperSecret1")
    b = hash_password("SuperSecret1")
    assert a != b


def test_register_success(client):
    email = f"reg{uuid.uuid4().hex[:8]}@example.com"
    response = client.post("/api/auth/register", json={
        "name": "New User", "email": email,
        "password": "StrongPass1", "confirm_password": "StrongPass1",
    })
    assert response.status_code == 201
    assert response.json()["user"]["email"] == email
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


def test_register_weak_password_rejected(client):
    response = client.post("/api/auth/register", json={
        "name": "Weak User", "email": "weak@example.com",
        "password": "password1", "confirm_password": "password1",
    })
    assert response.status_code == 400
    assert "uppercase" in response.json()["detail"]


def test_register_password_mismatch(client):
    response = client.post("/api/auth/register", json={
        "name": "Mismatch", "email": "mismatch@example.com",
        "password": "StrongPass1", "confirm_password": "StrongPass2",
    })
    assert response.status_code == 400
    assert "do not match" in response.json()["detail"]


def test_register_duplicate_email(client):
    email = f"dup{uuid.uuid4().hex[:8]}@example.com"
    payload = {"name": "Dup", "email": email,
               "password": "StrongPass1", "confirm_password": "StrongPass1"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_login_success(client):
    email = f"login{uuid.uuid4().hex[:8]}@example.com"
    password = "StrongPass1"
    client.post("/api/auth/register", json={
        "name": "Login User", "email": email,
        "password": password, "confirm_password": password,
    })
    response = client.post("/api/auth/login", json={
        "email": email, "password": password})
    assert response.status_code == 200
    assert response.json()["user"]["email"] == email
    assert "access_token" in response.cookies


def test_login_wrong_password(client):
    email = f"badpw{uuid.uuid4().hex[:8]}@example.com"
    client.post("/api/auth/register", json={
        "name": "Bad Pw", "email": email,
        "password": "StrongPass1", "confirm_password": "StrongPass1",
    })
    response = client.post("/api/auth/login", json={
        "email": email, "password": "WrongPass1"})
    assert response.status_code == 401


def test_me_requires_auth(client):
    assert client.get("/api/auth/me").status_code == 401


def test_me_returns_profile(client, auth_headers):
    response = client.get("/api/auth/me", cookies=auth_headers["cookies"])
    assert response.status_code == 200
    assert response.json()["name"] == "Test User"


def test_logout_revokes_session(client, auth_headers):
    response = client.post("/api/auth/logout", cookies=auth_headers["cookies"])
    assert response.status_code == 200
    assert "access_token" not in response.cookies
    refresh = auth_headers["cookies"].get("refresh_token")
    assert refresh is not None

    with SessionLocal() as db:
        row = db.scalar(select(RefreshToken).where(
            RefreshToken.token_hash == hashlib.sha256(
                refresh.encode()).hexdigest()))
        assert row is not None and row.revoked_at is not None


def test_refresh_rotation(client, auth_headers):
    old_refresh = auth_headers["cookies"].get("refresh_token")
    response = client.post("/api/auth/refresh", cookies={
        "refresh_token": old_refresh})
    assert response.status_code == 200
    new_refresh = response.cookies.get("refresh_token")
    assert new_refresh and new_refresh != old_refresh

    again = client.post("/api/auth/refresh", cookies={"refresh_token": old_refresh})
    assert again.status_code == 401


def test_change_password(client, auth_headers):
    response = client.post("/api/users/change-password", json={
        "old_password": "StrongPass1", "new_password": "NewStrongPass2",
    }, cookies=auth_headers["cookies"])
    assert response.status_code == 200

    login = client.post("/api/auth/login", json={
        "email": "test@example.com", "password": "StrongPass1"})
    assert login.status_code == 401
