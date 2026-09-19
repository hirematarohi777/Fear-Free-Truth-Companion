import pytest
import time
from app.core.security import (
    hash_password,
    verify_password,
    generate_opaque_token,
    hash_token,
    generate_csrf_token,
    verify_csrf_token,
    rate_limiter
)


def test_argon2id_password_hashing():
    raw = "SecureP@ssw0rd!123"
    hashed = hash_password(raw)
    assert hashed.startswith("$argon2id$")
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_csrf_token_verification():
    session_id = "sess_12345678"
    token = generate_csrf_token(session_id)
    
    # Valid token for same session
    assert verify_csrf_token(token, session_id) is True

    # Invalid session mismatch
    assert verify_csrf_token(token, "different_session_999") is False

    # Tampered signature
    tampered = token[:-4] + "abcd"
    assert verify_csrf_token(tampered, session_id) is False

    # Expired token
    assert verify_csrf_token(token, session_id, max_age_seconds=-1) is False


def test_rate_limiter():
    key = f"test_user_{int(time.time())}"
    # Max 3 requests in 10 seconds
    assert rate_limiter.is_allowed(key, max_requests=3, window_seconds=10)[0] is True
    assert rate_limiter.is_allowed(key, max_requests=3, window_seconds=10)[0] is True
    assert rate_limiter.is_allowed(key, max_requests=3, window_seconds=10)[0] is True

    # 4th request must be blocked
    allowed, retry_after = rate_limiter.is_allowed(key, max_requests=3, window_seconds=10)
    assert allowed is False
    assert retry_after > 0
