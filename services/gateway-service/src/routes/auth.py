"""Authentication routes: login, register, refresh, logout."""
import logging

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.config.settings import get_settings
from shared.models.orm import User
from shared.models.schemas import LoginRequest, TokenPair, UserCreate, UserResponse
from shared.utils.database import get_db
from shared.utils.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    password_hash,
    password_verify,
    validate_password_strength,
)

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


async def _get_redis() -> aioredis.Redis:
    return aioredis.from_url(settings.redis_url, decode_responses=True)


@router.post("/login", response_model=TokenPair)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return JWT tokens."""
    result = await db.execute(select(User).where(User.email == request.email.lower()))
    user = result.scalar_one_or_none()

    # Constant-time: always verify even if user not found to prevent timing attacks
    _DUMMY_HASH = "$2b$12$LJ3m4ys3L3Kj5ZI6v6K9/.jQ8X8F7z9Q8U0V1Y2W3X4Z5A6B7C8D9"
    if user is None:
        password_verify("dummy", _DUMMY_HASH)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not password_verify(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id)

    logger.info("User logged in: user_id=%s", user.id)

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    # Check password strength
    is_valid, msg = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg,
        )

    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email.lower())
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=user_data.email.lower(),
        password_hash=password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role.value if hasattr(user_data.role, "value") else user_data.role,
        organization=user_data.organization,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    logger.info("User registered: user_id=%s email=%s", user.id, user.email)

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        organization=user.organization,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh_token(request: Request, db: AsyncSession = Depends(get_db)):
    """Refresh access token using a valid refresh token."""
    body = await request.json()
    token = body.get("refresh_token", "")

    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    jti = payload.get("jti")
    if not jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Check jti against Redis blacklist
    try:
        redis = await _get_redis()
        is_blacklisted = await redis.get(f"token_blacklist:{jti}")
        await redis.close()
        if is_blacklisted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
            )
    except HTTPException:
        raise
    except Exception:
        # If Redis is down, allow the refresh (fail open for availability)
        pass

    user_id = payload.get("sub")
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Blacklist the old refresh token
    try:
        redis = await _get_redis()
        ttl = payload.get("exp", 0) - payload.get("iat", 0)
        await redis.setex(f"token_blacklist:{jti}", max(ttl, 1), "revoked")
        await redis.close()
    except Exception:
        pass

    new_access = create_access_token(user.id, user.role)
    new_refresh = create_refresh_token(user.id)

    return TokenPair(access_token=new_access, refresh_token=new_refresh)


@router.post("/logout")
async def logout(request: Request):
    """Invalidate refresh token by adding jti to Redis blacklist."""
    body = await request.json()
    token = body.get("refresh_token", "")

    try:
        payload = decode_token(token)
    except Exception:
        # Even if token is invalid, return success (don't leak info)
        return {"message": "Logged out successfully"}

    jti = payload.get("jti")
    if jti:
        try:
            redis = await _get_redis()
            ttl = payload.get("exp", 0) - payload.get("iat", 0)
            await redis.setex(f"token_blacklist:{jti}", max(ttl, 1), "revoked")
            await redis.close()
        except Exception:
            pass

    return {"message": "Logged out successfully"}
