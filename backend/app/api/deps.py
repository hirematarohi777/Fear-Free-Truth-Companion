from datetime import datetime, timezone
from typing import Optional
from fastapi import Request, HTTPException, status, Depends
from bson import ObjectId
from app.core.config import settings
from app.core.security import hash_token, verify_csrf_token
from app.db.mongo import get_db


class AuthenticatedUser:
    def __init__(self, user_id: str, email: str, display_name: str, session_id: str):
        self.id = user_id
        self.email = email
        self.displayName = display_name
        self.sessionId = session_id


async def get_current_user(request: Request) -> AuthenticatedUser:
    """
    Extract opaque session token from HttpOnly cookie or Authorization header,
    hash it, and look up active session in MongoDB.
    """
    token = request.cookies.get(settings.COOKIE_NAME)
    if not token:
        # Fallback to Bearer token header if present
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. No session cookie found."
        )

    db = get_db()
    hashed = hash_token(token)
    now = datetime.now(timezone.utc)

    session = await db.sessions.find_one({"tokenHash": hashed, "expiresAt": {"$gt": now}})
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or is invalid. Please log in again."
        )

    user = await db.users.find_one({"_id": ObjectId(session["userId"])})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Associated user account no longer exists."
        )

    return AuthenticatedUser(
        user_id=str(user["_id"]),
        email=user["emailNormalized"],
        display_name=user.get("displayName", "User"),
        session_id=str(session["_id"])
    )


async def verify_csrf(request: Request, user: AuthenticatedUser = Depends(get_current_user)):
    """
    Verify CSRF token for state-changing HTTP methods.
    Checks X-CSRF-Token header against HMAC-SHA256 signature.
    """
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        csrf_header = request.headers.get("X-CSRF-Token")
        if not csrf_header:
            csrf_cookie = request.cookies.get(settings.CSRF_COOKIE_NAME)
            csrf_header = csrf_cookie

        if not csrf_header or not verify_csrf_token(csrf_header, user.sessionId):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF verification failed or token expired."
            )
    return True
