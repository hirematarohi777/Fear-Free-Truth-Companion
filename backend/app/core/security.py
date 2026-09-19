import hashlib
import hmac
import secrets
import time
from collections import defaultdict
from typing import Optional, Tuple
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from app.core.config import settings

# Initialize Argon2id password hasher with recommended parameters
ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,  # 64 MB
    parallelism=4,
    hash_len=32,
    salt_len=16
)


def hash_password(password: str) -> str:
    """Hash password using Argon2id."""
    return ph.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against Argon2id hash."""
    try:
        return ph.verify(hashed, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def generate_opaque_token(length_bytes: int = 32) -> str:
    """Generate a cryptographically random, URL-safe opaque token."""
    return secrets.token_urlsafe(length_bytes)


def hash_token(token: str) -> str:
    """Hash an opaque token using SHA-256 for database storage.
    Session tokens and invitation tokens are NEVER stored in plaintext.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_csrf_token(session_id: str) -> str:
    """Generate an HMAC-SHA256 CSRF token tied to the session."""
    message = f"{session_id}:{int(time.time())}:{secrets.token_hex(8)}"
    signature = hmac.new(
        settings.CSRF_SECRET.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    return f"{message}:{signature}"


def verify_csrf_token(csrf_token: str, session_id: str, max_age_seconds: int = 86400) -> bool:
    """Verify an HMAC-SHA256 CSRF token."""
    try:
        parts = csrf_token.split(":")
        if len(parts) != 4:
            return False
        token_session_id, timestamp_str, salt, signature = parts
        
        # Ensure token belongs to current session
        if not hmac.compare_digest(token_session_id, session_id):
            return False
            
        timestamp = int(timestamp_str)
        if time.time() - timestamp > max_age_seconds:
            return False
            
        message = f"{token_session_id}:{timestamp_str}:{salt}"
        expected_sig = hmac.new(
            settings.CSRF_SECRET.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_sig)
    except Exception:
        return False


class SimpleRateLimiter:
    """In-memory sliding window rate limiter for login and upload actions."""
    def __init__(self):
        self._records = defaultdict(list)

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
        now = time.time()
        window_start = now - window_seconds
        # Evict old records
        self._records[key] = [t for t in self._records[key] if t > window_start]
        if len(self._records[key]) >= max_requests:
            retry_after = int(self._records[key][0] + window_seconds - now)
            return False, max(1, retry_after)
        self._records[key].append(now)
        return True, 0

    def reset(self, key: str) -> None:
        if key in self._records:
            del self._records[key]


rate_limiter = SimpleRateLimiter()
