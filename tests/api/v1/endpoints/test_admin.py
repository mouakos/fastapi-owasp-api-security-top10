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


class TestAdminListUsersSuccess:
    async def test_admin_can_list_users(
        self, client: AsyncClient, admin_auth_headers: dict[str, str]
    ) -> None:
        response = await client.get("/api/v1/admin/users", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    async def test_admin_list_users_returns_page_shape(
        self, client: AsyncClient, admin_auth_headers: dict[str, str]
    ) -> None:
        response = await client.get("/api/v1/admin/users?page=1&size=5", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 5


class TestAdminListItemsSuccess:
    async def test_admin_can_list_all_items(
        self, client: AsyncClient, admin_auth_headers: dict[str, str]
    ) -> None:
        response = await client.get("/api/v1/admin/items", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data


class TestAdminUpdateUserSuccess:
    async def test_admin_can_deactivate_user(
        self,
        client: AsyncClient,
        admin_auth_headers: dict[str, str],
        registered_user: dict[str, str],
    ) -> None:
        # Get the registered user's ID first
        login_resp = await client.post(
            "/api/v1/auth/token",
            data={"username": registered_user["email"], "password": registered_user["password"]},
        )
        token = login_resp.json()["access_token"]
        me_resp = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
        user_id = me_resp.json()["id"]

        response = await client.patch(
            f"/api/v1/admin/users/{user_id}",
            json={"is_active": False},
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False

    async def test_admin_update_nonexistent_user_returns_404(
        self, client: AsyncClient, admin_auth_headers: dict[str, str]
    ) -> None:
        from uuid import uuid4

        response = await client.patch(
            f"/api/v1/admin/users/{uuid4()}",
            json={"is_active": False},
            headers=admin_auth_headers,
        )
        assert response.status_code == 404
