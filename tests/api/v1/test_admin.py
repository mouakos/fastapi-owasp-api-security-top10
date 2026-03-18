"""API tests for /admin endpoints (OWASP API5: BFLA enforcement)."""

from uuid import uuid4

from httpx import AsyncClient


class TestAdminListUsers:
    async def test_requires_auth(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/admin/users")
        assert response.status_code == 401

    async def test_regular_user_is_forbidden(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """OWASP API5: BFLA — regular users must not access admin endpoints."""
        response = await client.get("/api/v1/admin/users", headers=auth_headers)
        assert response.status_code == 403

    async def test_regular_user_cannot_access_admin_items(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.get("/api/v1/admin/items", headers=auth_headers)
        assert response.status_code == 403


class TestAdminUpdateUser:
    async def test_regular_user_cannot_update_other_user(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """OWASP API5: BFLA — regular users cannot use admin update endpoint."""
        response = await client.patch(
            f"/api/v1/admin/users/{uuid4()}",
            json={"role": "admin"},
            headers=auth_headers,
        )
        assert response.status_code == 403
