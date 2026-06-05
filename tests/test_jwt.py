import uuid

import pytest

from app.core.jwt import create_access_token, decode_access_token


def test_access_token_roundtrip() -> None:
    user_id = uuid.uuid4()
    token = create_access_token(user_id, "admin")
    payload = decode_access_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["role"] == "admin"
    assert payload["type"] == "access"


def test_invalid_access_token_is_rejected() -> None:
    with pytest.raises(ValueError):
        decode_access_token("not-a-jwt")
