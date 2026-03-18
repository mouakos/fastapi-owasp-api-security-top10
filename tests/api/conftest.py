"""API layer fixtures: AsyncClient with test DB dependency overrides."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_uow
from app.main import app
from app.persistence.uow.sqlmodel_uow import SqlModelUnitOfWork


@pytest.fixture
async def client(session_factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncClient]:
    """AsyncClient wired to the test in-memory SQLite database."""

    async def override_get_uow() -> AsyncGenerator[SqlModelUnitOfWork]:
        _uow = SqlModelUnitOfWork(session_factory)
        async with _uow:
            yield _uow

    app.dependency_overrides[get_uow] = override_get_uow
    app.state.limiter.enabled = False
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.state.limiter.enabled = True
    app.dependency_overrides.clear()


@pytest.fixture
async def registered_user(client: AsyncClient) -> dict[str, str]:
    """Register a fresh user and return their credentials."""
    from uuid import uuid4

    suffix = uuid4().hex[:8]
    payload = {
        "email": f"user_{suffix}@example.com",
        "username": f"user_{suffix}",
        "password": "Password1!",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    return payload


@pytest.fixture
async def auth_headers(client: AsyncClient, registered_user: dict[str, str]) -> dict[str, str]:
    """Return Bearer auth headers for a registered user."""
    response = await client.post(
        "/api/v1/auth/token",
        data={
            "username": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
