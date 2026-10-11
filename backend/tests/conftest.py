"""Pytest fixtures shared by all tests."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def _isolate_database(tmp_path_factory):
    """Use a temporary SQLite database so tests don't touch production data."""
    db_path = tmp_path_factory.mktemp("data") / "test.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["APP_ENV"] = "testing"
    os.environ["ENABLE_DEMO_MODE"] = "true"
    os.environ["SECRET_KEY"] = "test-secret-key-for-pytest-only"
    os.environ["RATE_LIMIT_PER_MINUTE"] = "10000"  # disable in tests
    # Force re-import of settings
    from app.utils.config import get_settings

    get_settings.cache_clear()
    yield


@pytest.fixture(scope="session")
def client():
    from app.main import create_app

    app = create_app()
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def seeded_user():
    """Create a demo user and return credentials."""
    from app.database.seed import ensure_base_data

    ensure_base_data()
    return {"username": "demo-operator", "password": "demo123"}


@pytest.fixture(scope="session")
def auth_token(client, seeded_user):
    res = client.post(
        "/api/auth/login",
        json={"username": seeded_user["username"], "password": seeded_user["password"]},
    )
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


@pytest.fixture()
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture()
def sample_png():
    """Generate a tiny 64x64 grayscale PNG in memory."""
    import io

    import cv2
    import numpy as np

    img = (np.random.rand(64, 64) * 255).astype(np.uint8)
    ok, buf = cv2.imencode(".png", img)
    assert ok
    return buf.tobytes()