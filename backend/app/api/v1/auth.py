from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, status, Response, Request, Depends
from bson import ObjectId
from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    generate_opaque_token,
    hash_token,
    generate_csrf_token,
    rate_limiter
)
from app.schemas.auth import UserRegisterRequest, UserLoginRequest, UserResponse, CsrfTokenResponse
from app.db.mongo import get_db
from app.api.deps import get_current_user, AuthenticatedUser


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(req: UserRegisterRequest, response: Response):
    db = get_db()
    email_norm = req.email.strip().lower()

    existing = await db.users.find_one({"emailNormalized": email_norm})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    now = datetime.now(timezone.utc)
    user_doc = {
        "emailNormalized": email_norm,
        "passwordHash": hash_password(req.password),
        "displayName": req.displayName.strip(),
        "createdAt": now,
        "updatedAt": now
    }

    res = await db.users.insert_one(user_doc)
    user_id = str(res.inserted_id)

    # Automatically create session
    raw_token = generate_opaque_token()
    token_hash = hash_token(raw_token)
    expires_at = now + timedelta(hours=settings.SESSION_TTL_HOURS)

    session_doc = {
        "userId": user_id,
        "tokenHash": token_hash,
        "expiresAt": expires_at,
        "createdAt": now
    }
    session_res = await db.sessions.insert_one(session_doc)
    session_id = str(session_res.inserted_id)

    # Set HttpOnly Session Cookie
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=raw_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.SESSION_TTL_HOURS * 3600,
        path="/"
    )

    csrf_token = generate_csrf_token(session_id)
    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,  # Accessible to frontend for header submission
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.SESSION_TTL_HOURS * 3600,
        path="/"
    )

    return UserResponse(
        id=user_id,
        email=email_norm,
        displayName=req.displayName.strip(),
        createdAt=now
    )


@router.post("/login", response_model=UserResponse)
async def login_user(req: UserLoginRequest, request: Request, response: Response):
    # Rate limit by client IP: max 10 attempts per minute
    client_ip = request.client.host if request.client else "unknown"
    allowed, retry_after = rate_limiter.is_allowed(f"login:{client_ip}", max_requests=10, window_seconds=60)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Please wait {retry_after} seconds before trying again."
        )

    db = get_db()
    email_norm = req.email.strip().lower()
    user = await db.users.find_one({"emailNormalized": email_norm})

    if not user or not verify_password(req.password, user["passwordHash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email address or password."
        )

    now = datetime.now(timezone.utc)
    raw_token = generate_opaque_token()
    token_hash = hash_token(raw_token)
    expires_at = now + timedelta(hours=settings.SESSION_TTL_HOURS)

    session_doc = {
        "userId": str(user["_id"]),
        "tokenHash": token_hash,
        "expiresAt": expires_at,
        "createdAt": now
    }
    session_res = await db.sessions.insert_one(session_doc)
    session_id = str(session_res.inserted_id)

    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=raw_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.SESSION_TTL_HOURS * 3600,
        path="/"
    )

    csrf_token = generate_csrf_token(session_id)
    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.SESSION_TTL_HOURS * 3600,
        path="/"
    )

    return UserResponse(
        id=str(user["_id"]),
        email=user["emailNormalized"],
        displayName=user.get("displayName", "User"),
        createdAt=user["createdAt"]
    )


@router.post("/logout")
async def logout_user(request: Request, response: Response):
    token = request.cookies.get(settings.COOKIE_NAME)
    if token:
        db = get_db()
        hashed = hash_token(token)
        await db.sessions.delete_one({"tokenHash": hashed})

    response.delete_cookie(settings.COOKIE_NAME, path="/")
    response.delete_cookie(settings.CSRF_COOKIE_NAME, path="/")
    return {"message": "Logged out successfully."}


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(user: AuthenticatedUser = Depends(get_current_user)):
    return UserResponse(
        id=user.id,
        email=user.email,
        displayName=user.displayName,
        createdAt=datetime.now(timezone.utc)
    )


@router.get("/csrf", response_model=CsrfTokenResponse)
async def get_csrf_token(response: Response, user: AuthenticatedUser = Depends(get_current_user)):
    csrf_token = generate_csrf_token(user.sessionId)
    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.SESSION_TTL_HOURS * 3600,
        path="/"
    )
    return CsrfTokenResponse(csrfToken=csrf_token)
