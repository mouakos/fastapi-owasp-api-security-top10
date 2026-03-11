"""API v1 router composition module."""

from fastapi import APIRouter

from .endpoints.auth import router as auth_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
