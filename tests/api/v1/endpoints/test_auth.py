"""API tests for /auth/register and /auth/token endpoints."""

from uuid import uuid4

from httpx import AsyncClient


def unique_user() -> dict[str, str]:
    suffix = uuid4().hex[:8]
    return {
        "email": f"user_{suffix}@example.com",
        "username": f"user_{suffix}",
        "password": "Password1!",
    }


class TestRegister:
    async def test_register_returns_201(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/auth/register", json=unique_user())
        assert response.status_code == 201

    async def test_register_returns_user_data(self, client: AsyncClient) -> None:
        user = unique_user()
        response = await client.post("/api/v1/auth/register", json=user)
        data = response.json()
        assert data["email"] == user["email"]
        assert data["username"] == user["username"]

    async def test_register_does_not_expose_password(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/auth/register", json=unique_user())
        data = response.json()
        assert "password" not in data
        assert "hashed_password" not in data

    async def test_duplicate_email_returns_409(
        self, client: AsyncClient, registered_user: dict[str, str]
    ) -> None:
        payload = {**registered_user, "username": "different_user"}
        response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 409

    async def test_duplicate_username_returns_409(
        self, client: AsyncClient, registered_user: dict[str, str]
    ) -> None:
        payload = {**registered_user, "email": "other@example.com"}
        response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 409

    async def test_weak_password_returns_422(self, client: AsyncClient) -> None:
        user = unique_user()
        user["password"] = "weak"
        response = await client.post("/api/v1/auth/register", json=user)
        assert response.status_code == 422


class TestLogin:
    async def test_login_returns_access_token(
        self, client: AsyncClient, registered_user: dict[str, str]
    ) -> None:
        response = await client.post(
            "/api/v1/auth/token",
            data={"username": registered_user["email"], "password": registered_user["password"]},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    async def test_login_by_username(
        self, client: AsyncClient, registered_user: dict[str, str]
    ) -> None:
        response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": registered_user["username"],
                "password": registered_user["password"],
            },
        )
        assert response.status_code == 200

    async def test_wrong_password_returns_401(
        self, client: AsyncClient, registered_user: dict[str, str]
    ) -> None:
        response = await client.post(
            "/api/v1/auth/token",
            data={"username": registered_user["email"], "password": "WrongPass1!"},
        )
        assert response.status_code == 401

    async def test_nonexistent_user_returns_401(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/token",
            data={"username": "ghost@example.com", "password": "Password1!"},
        )
        assert response.status_code == 401


class TestExceptionHandlers:
    async def test_unknown_route_returns_404(self, client: AsyncClient) -> None:
        """FastAPI raises HTTPException(404) for unknown routes — exercises http_exception_handler."""
        response = await client.get("/api/v1/does-not-exist")
        assert response.status_code == 404

    async def test_method_not_allowed_returns_405(self, client: AsyncClient) -> None:
        """FastAPI raises HTTPException(405) for wrong HTTP method — exercises http_exception_handler."""
        response = await client.delete("/api/v1/auth/register")
        assert response.status_code == 405

    async def test_missing_token_returns_401(self, client: AsyncClient) -> None:
        """No Authorization header at all — exercises AuthenticationError path in get_current_user."""
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 401

    async def test_token_with_non_uuid_sub_returns_401(self, client: AsyncClient) -> None:
        """JWT with a valid string but non-UUID sub — exercises UUID parse failure in get_current_user."""
        from app.core.security.jwt import create_access_token

        token = create_access_token({"sub": "not-a-uuid-string"})
        response = await client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401
