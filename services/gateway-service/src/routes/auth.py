"""Authentication routes."""
from fastapi import APIRouter, HTTPException, status

from shared.models.schemas import LoginRequest, TokenPair, UserCreate, UserResponse

router = APIRouter()


@router.post("/login", response_model=TokenPair)
async def login(request: LoginRequest):
    """Authenticate user and return JWT tokens."""
    # TODO: Implement with actual DB lookup and bcrypt verification
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not yet implemented")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    """Register a new user."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not yet implemented")


@router.post("/refresh", response_model=TokenPair)
async def refresh_token(refresh_token: str):
    """Refresh access token."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not yet implemented")


@router.post("/logout")
async def logout():
    """Invalidate refresh token."""
    return {"message": "Logged out successfully"}
