"""API tests for /users/me endpoints."""

from uuid import uuid4

from httpx import AsyncClient


class TestGetMe:
    async def test_requires_auth(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 401

    async def test_returns_current_user_profile(
        self, client: AsyncClient, auth_headers: dict[str, str], registered_user: dict[str, str]
    ) -> None:
        response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == registered_user["email"]
        assert data["username"] == registered_user["username"]

    async def test_response_does_not_expose_password(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.get("/api/v1/users/me", headers=auth_headers)
        data = response.json()
        assert "password" not in data
        assert "hashed_password" not in data

    async def test_response_does_not_expose_security_fields(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """OWASP API3: Excessive data exposure check."""
        response = await client.get("/api/v1/users/me", headers=auth_headers)
        data = response.json()
        assert "failed_login_attempts" not in data
        assert "locked_until" not in data


class TestUpdateMe:
    async def test_requires_auth(self, client: AsyncClient) -> None:
        response = await client.patch("/api/v1/users/me", json={"username": "newname"})
        assert response.status_code == 401

    async def test_update_username_succeeds(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        new_username = f"updated_{uuid4().hex[:8]}"
        response = await client.patch(
            "/api/v1/users/me", json={"username": new_username}, headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["username"] == new_username

    async def test_cannot_update_role(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """OWASP API3: Users must not be able to escalate their own role."""
        response = await client.patch(
            "/api/v1/users/me", json={"role": "admin"}, headers=auth_headers
        )
        # Either 422 (field rejected) or 200 with role unchanged
        if response.status_code == 200:
            assert response.json()["role"] != "admin"
