"""API v1 router composition module."""

from fastapi import APIRouter

from .endpoints.admin import router as admin_router
from .endpoints.auth import router as auth_router
from .endpoints.items import router as items_router
from .endpoints.users import router as users_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
api_v1_router.include_router(users_router, prefix="/api/v1/users", tags=["users"])
api_v1_router.include_router(items_router, prefix="/api/v1/items", tags=["items"])
api_v1_router.include_router(admin_router, prefix="/api/v1/admin", tags=["admin"])
