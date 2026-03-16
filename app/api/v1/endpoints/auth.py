"""Authentication router for API v1."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.rate_limiter import limiter
from app.api.v1.schemas.auth import Token
from app.api.v1.schemas.user import UserCreate, UserResponse
from app.db.models.user import User
from app.dependencies import UserServiceDependency

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
@limiter.limit("10/minute")
async def register(request: Request, data: UserCreate, user_service: UserServiceDependency) -> User:  # noqa: ARG001
    """Register a new user account."""
    return await user_service.create_user(data)


@router.post(
    "/token", response_model=Token, summary="Authenticate a user and return an access token"
)
@limiter.limit("10/minute")
async def login(
    request: Request,  # noqa: ARG001
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: UserServiceDependency,
) -> Token:
    """Authenticate a user and return an access token."""
    return await user_service.authenticate_user(form_data.username, form_data.password)
