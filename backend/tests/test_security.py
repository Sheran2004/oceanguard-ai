"""Security utility tests."""
from __future__ import annotations

import pytest

from app.utils.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_round_trip():
    plain = "secret123"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("wrong", hashed) is False


def test_jwt_round_trip():
    token = create_access_token("alice", extra={"role": "admin"})
    payload = decode_token(token)
    assert payload["sub"] == "alice"
    assert payload["role"] == "admin"


def test_jwt_invalid_token_rejected():
    with pytest.raises(ValueError):
        decode_token("not-a-token")