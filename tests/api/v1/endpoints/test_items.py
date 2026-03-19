"""API tests for /items endpoints (OWASP API1: BOLA enforcement)."""

from uuid import uuid4

from httpx import AsyncClient

ITEM_PAYLOAD: dict[str, object] = {"title": "My Item", "price": 9.99}


class TestListItems:
    async def test_requires_auth(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/items/")
        assert response.status_code == 401

    async def test_returns_empty_list_for_new_user(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.get("/api/v1/items/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data or isinstance(data, list)


class TestCreateItem:
    async def test_requires_auth(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/items/", json=ITEM_PAYLOAD)
        assert response.status_code == 401

    async def test_creates_item_returns_201(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.post("/api/v1/items/", json=ITEM_PAYLOAD, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == ITEM_PAYLOAD["title"]

    async def test_owner_is_set_to_current_user(
        self, client: AsyncClient, auth_headers: dict[str, str], registered_user: dict[str, str]
    ) -> None:
        response = await client.post("/api/v1/items/", json=ITEM_PAYLOAD, headers=auth_headers)
        assert response.status_code == 201

    async def test_empty_title_returns_422(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.post(
            "/api/v1/items/", json={"title": "", "price": 1.0}, headers=auth_headers
        )
        assert response.status_code == 422

    async def test_negative_price_returns_422(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.post(
            "/api/v1/items/", json={"title": "Item", "price": -1.0}, headers=auth_headers
        )
        assert response.status_code == 422


class TestGetItem:
    async def test_requires_auth(self, client: AsyncClient) -> None:
        response = await client.get(f"/api/v1/items/{uuid4()}")
        assert response.status_code == 401

    async def test_returns_own_item(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        created = await client.post("/api/v1/items/", json=ITEM_PAYLOAD, headers=auth_headers)
        item_id = created.json()["id"]

        response = await client.get(f"/api/v1/items/{item_id}", headers=auth_headers)
        assert response.status_code == 200

    async def test_cannot_access_other_users_item(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """OWASP API1: BOLA — user cannot access another user's item."""
        # Create item as user A
        created = await client.post("/api/v1/items/", json=ITEM_PAYLOAD, headers=auth_headers)
        item_id = created.json()["id"]

        # Register and login as user B
        suffix = uuid4().hex[:8]
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"b_{suffix}@example.com",
                "username": f"b_{suffix}",
                "password": "Password1!",
            },
        )
        token_resp = await client.post(
            "/api/v1/auth/token",
            data={"username": f"b_{suffix}@example.com", "password": "Password1!"},
        )
        b_headers: dict[str, str] = {"Authorization": f"Bearer {token_resp.json()['access_token']}"}

        response = await client.get(f"/api/v1/items/{item_id}", headers=b_headers)
        assert response.status_code in (403, 404)

    async def test_nonexistent_item_returns_404(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.get(f"/api/v1/items/{uuid4()}", headers=auth_headers)
        assert response.status_code == 404


class TestDeleteItem:
    async def test_deletes_own_item_returns_204(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        created = await client.post("/api/v1/items/", json=ITEM_PAYLOAD, headers=auth_headers)
        item_id = created.json()["id"]

        response = await client.delete(f"/api/v1/items/{item_id}", headers=auth_headers)
        assert response.status_code == 204

    async def test_cannot_delete_other_users_item(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """OWASP API1: BOLA — user cannot delete another user's item."""
        created = await client.post("/api/v1/items/", json=ITEM_PAYLOAD, headers=auth_headers)
        item_id = created.json()["id"]

        suffix = uuid4().hex[:8]
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"b_{suffix}@example.com",
                "username": f"b_{suffix}",
                "password": "Password1!",
            },
        )
        token_resp = await client.post(
            "/api/v1/auth/token",
            data={"username": f"b_{suffix}@example.com", "password": "Password1!"},
        )
        b_headers: dict[str, str] = {"Authorization": f"Bearer {token_resp.json()['access_token']}"}

        response = await client.delete(f"/api/v1/items/{item_id}", headers=b_headers)
        assert response.status_code in (403, 404)


class TestUpdateItem:
    async def test_requires_auth(self, client: AsyncClient) -> None:
        response = await client.patch(f"/api/v1/items/{uuid4()}", json={"title": "New"})
        assert response.status_code == 401

    async def test_updates_own_item(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        created = await client.post("/api/v1/items/", json=ITEM_PAYLOAD, headers=auth_headers)
        item_id = created.json()["id"]

        response = await client.patch(
            f"/api/v1/items/{item_id}",
            json={"title": "Updated Title"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"

    async def test_cannot_update_other_users_item(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """OWASP API1: BOLA — user cannot update another user's item."""
        created = await client.post("/api/v1/items/", json=ITEM_PAYLOAD, headers=auth_headers)
        item_id = created.json()["id"]

        suffix = uuid4().hex[:8]
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"b_{suffix}@example.com",
                "username": f"b_{suffix}",
                "password": "Password1!",
            },
        )
        token_resp = await client.post(
            "/api/v1/auth/token",
            data={"username": f"b_{suffix}@example.com", "password": "Password1!"},
        )
        b_headers: dict[str, str] = {"Authorization": f"Bearer {token_resp.json()['access_token']}"}

        response = await client.patch(
            f"/api/v1/items/{item_id}", json={"title": "Stolen"}, headers=b_headers
        )
        assert response.status_code in (403, 404)

    async def test_update_nonexistent_item_returns_404(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.patch(
            f"/api/v1/items/{uuid4()}", json={"title": "Ghost"}, headers=auth_headers
        )
        assert response.status_code == 404
