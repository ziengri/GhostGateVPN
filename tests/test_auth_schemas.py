import pytest
from pydantic import ValidationError

from app.schemas.auth import LoginRequest, RegisterRequest


def test_register_requires_phone_number_with_ru_format() -> None:
    payload = RegisterRequest(email="user@example.com", phone_number="+70000000000", password="password123")
    assert payload.phone_number == "+70000000000"

    with pytest.raises(ValidationError):
        RegisterRequest(email="user@example.com", phone_number="70000000000", password="password123")

    with pytest.raises(ValidationError):
        RegisterRequest(email="user@example.com", phone_number="+7999", password="password123")


def test_login_does_not_require_phone_number() -> None:
    payload = LoginRequest(email="user@example.com", password="password123")
    assert payload.email == "user@example.com"
