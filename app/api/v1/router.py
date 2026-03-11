"""API v1 router composition module."""

from fastapi import APIRouter

from .endpoints.auth import router as auth_router
from .endpoints.users import router as users_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
api_v1_router.include_router(users_router, prefix="/api/v1/users", tags=["users"])
