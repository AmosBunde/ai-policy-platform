"""User management routes."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/me")
async def get_current_user():
    """Get current authenticated user profile."""
    # TODO: Implement with JWT dependency
    return {"message": "Not yet implemented"}


@router.get("/")
async def list_users():
    """List all users (admin only)."""
    return {"message": "Not yet implemented"}
