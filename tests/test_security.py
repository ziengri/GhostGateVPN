from app.core.security import hash_password, hash_token, new_opaque_token, verify_password


def test_password_hash_roundtrip() -> None:
    hashed = hash_password("correct horse battery staple")
    assert hashed != "correct horse battery staple"
    assert verify_password("correct horse battery staple", hashed)
    assert not verify_password("wrong password", hashed)


def test_token_hash_is_stable_and_not_plaintext() -> None:
    token = new_opaque_token()
    assert hash_token(token) == hash_token(token)
    assert hash_token(token) != token

