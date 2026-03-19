"""API endpoints for user-related operations."""

from fastapi import APIRouter

from app.api.deps import CurrentUserDependency, UserServiceDependency
from app.api.v1.schemas.user import UserResponse, UserUpdate
from app.persistence.models.user import User

router = APIRouter()

# ---------------------------------------------------------------------------
# Current-user profile
# ---------------------------------------------------------------------------


@router.get("/me", response_model=UserResponse, summary="Get my profile")
async def get_me(current_user: CurrentUserDependency) -> User:
    """Return the authenticated user's profile information."""
    return current_user


# ---------------------------------------------------------------------------
# API3: UserUpdate limits patchable fields to username only — role and
#       is_active are intentionally excluded to prevent privilege escalation.
# ---------------------------------------------------------------------------
@router.patch("/me", response_model=UserResponse, summary="Update my profile")
async def update_me(
    data: UserUpdate,
    current_user: CurrentUserDependency,
    user_service: UserServiceDependency,
) -> User:
    """Update the authenticated user's profile information."""
    return await user_service.update_user(current_user.id, data)  # type: ignore [arg-type]
