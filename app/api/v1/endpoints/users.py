"""API endpoints for user-related operations."""

from fastapi import APIRouter

from app.api.v1.schemas.user import UserResponse, UserUpdate
from app.db.models.user import User
from app.dependencies import CurrentUserDependency, UserServiceDependency

router = APIRouter()

# ---------------------------------------------------------------------------
# Current-user profile
# ---------------------------------------------------------------------------


@router.get("/me", response_model=UserResponse, summary="Get my profile")
async def get_me(current_user: CurrentUserDependency) -> User:
    """Return the authenticated user's profile information."""
    return current_user


@router.patch("/me", response_model=UserResponse, summary="Update my profile")
async def update_me(
    data: UserUpdate,
    current_user: CurrentUserDependency,
    user_service: UserServiceDependency,
) -> User:
    """Update the authenticated user's profile information."""
    return await user_service.update_user(current_user.id, data)  # type: ignore [arg-type]
