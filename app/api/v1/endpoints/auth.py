"""Authentication router for API v1."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.api.v1.schemas.auth import Token
from app.api.v1.schemas.user import UserCreate, UserResponse
from app.core.security import create_access_token
from app.db.models.user import User
from app.dependencies import UserServiceDependency

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: UserCreate, user_service: UserServiceDependency) -> User:
    """Register a new user account."""
    return await user_service.create_user(data.username, data.email, data.password)


@router.post("/token", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], user_service: UserServiceDependency
) -> Token:
    """Authenticate a user and return an access token."""
    user = await user_service.authenticate_user(form_data.username, form_data.password)
    access_token = create_access_token({"sub": str(user.id)})
    return Token(access_token=access_token)
