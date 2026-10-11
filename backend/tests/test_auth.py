"""Tests for /api/auth endpoints."""
from __future__ import annotations


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert "model" in body
    assert "version" in body


def test_login_success(client, seeded_user):
    res = client.post(
        "/api/auth/login",
        json={"username": seeded_user["username"], "password": seeded_user["password"]},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["token_type"] == "bearer"
    assert "access_token" in body
    assert body["user"]["username"] == seeded_user["username"]


def test_login_wrong_password(client, seeded_user):
    res = client.post(
        "/api/auth/login",
        json={"username": seeded_user["username"], "password": "wrong"},
    )
    assert res.status_code == 401


def test_me_requires_token(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401


def test_me_with_token(client, auth_headers):
    res = client.get("/api/auth/me", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["username"] == "demo-operator"


def test_register_creates_user(client):
    import uuid

    uname = f"newuser_{uuid.uuid4().hex[:8]}"
    payload = {
        "username": uname,
        "password": "secret123",
        "email": f"{uname}@oceanguard.example",
        "full_name": "New User",
    }

    res = client.post("/api/auth/register", json=payload)

    assert res.status_code == 201, res.text
    body = res.json()

    assert body["username"] == uname
    assert body["role"] == "operator"

    # Duplicate registration should fail.
    res2 = client.post("/api/auth/register", json=payload)
    assert res2.status_code == 409


def test_register_cannot_assign_admin_role(client):
    import uuid

    uname = f"attemptadmin_{uuid.uuid4().hex[:8]}"

    payload = {
        "username": uname,
        "password": "secret123",
        "email": f"{uname}@oceanguard.example",
        "role": "admin",
    }

    res = client.post("/api/auth/register", json=payload)

    # Depending on the schema configuration, the extra role field may
    # be ignored or rejected. It must never grant admin privileges.
    if res.status_code == 201:
        assert res.json()["role"] == "operator"
    else:
        assert res.status_code == 422

def test_password_validation(client):
    # Too short
    res = client.post(
        "/api/auth/register",
        json={"username": "weakuser", "password": "abc", "role": "operator"},
    )
    assert res.status_code == 422


def test_change_password(client, auth_headers, seeded_user):
    # First change to a new password
    res = client.post(
        "/api/auth/change-password",
        json={"current_password": seeded_user["password"], "new_password": "newpass123"},
        headers=auth_headers,
    )
    assert res.status_code == 200

    # Now log in with the new password
    res2 = client.post(
        "/api/auth/login",
        json={"username": seeded_user["username"], "password": "newpass123"},
    )
    assert res2.status_code == 200

    # Revert for other tests
    token = res2.json()["access_token"]
    client.post(
        "/api/auth/change-password",
        json={"current_password": "newpass123", "new_password": seeded_user["password"]},
        headers={"Authorization": f"Bearer {token}"},
    )