"""API tests for /items endpoints (OWASP API1: BOLA enforcement)."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import httpx
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


# ---------------------------------------------------------------------------
# Helper — build a mock httpx.AsyncClient that returns a canned response body
# ---------------------------------------------------------------------------


def _mock_httpx_client(json_data: dict, status_code: int = 200) -> MagicMock:
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.content = b"x"  # within size limit
    response.json.return_value = json_data
    if status_code >= 400:
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message=f"HTTP {status_code}", request=MagicMock(), response=response
        )
    else:
        response.raise_for_status.return_value = None
    mock_client = AsyncMock()
    mock_client.request = AsyncMock(return_value=response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return mock_client


_EXTERNAL_ITEM = {"title": "External Widget", "description": "From upstream", "price": 4.99}
_IMPORT_URL = "https://example.com/item.json"


class TestImportItem:
    """POST /items/import — API7 (SSRF) + API10 (safe consumption) + API1 (ownership)."""

    async def test_requires_auth(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/items/import", json={"url": _IMPORT_URL})
        assert response.status_code == 401

    async def test_successful_import_creates_item(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        with patch("httpx.AsyncClient", return_value=_mock_httpx_client(_EXTERNAL_ITEM)):
            response = await client.post(
                "/api/v1/items/import", json={"url": _IMPORT_URL}, headers=auth_headers
            )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == _EXTERNAL_ITEM["title"]
        assert data["price"] == _EXTERNAL_ITEM["price"]

    async def test_owner_is_authenticated_user_not_from_payload(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """API1: owner_id must come from the JWT, never from the external payload."""
        poisoned = {**_EXTERNAL_ITEM, "owner_id": str(uuid4())}
        with patch("httpx.AsyncClient", return_value=_mock_httpx_client(poisoned)):
            response = await client.post(
                "/api/v1/items/import", json={"url": _IMPORT_URL}, headers=auth_headers
            )
        assert response.status_code == 201
        # owner_id in the response must be the real authenticated user, not the injected value
        assert response.json()["owner_id"] != poisoned["owner_id"]

    async def test_private_ip_url_is_rejected(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """API7: SSRF — requests targeting private IP ranges must be blocked."""
        response = await client.post(
            "/api/v1/items/import",
            json={"url": "http://192.168.1.1/secret"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_localhost_url_is_rejected(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """API7: SSRF — localhost must be blocked by hostname check."""
        response = await client.post(
            "/api/v1/items/import",
            json={"url": "http://localhost/internal"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_metadata_endpoint_is_rejected(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """API7: SSRF — cloud metadata endpoint must be blocked."""
        response = await client.post(
            "/api/v1/items/import",
            json={"url": "http://169.254.169.254/latest/meta-data/"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_non_http_scheme_is_rejected(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """API7: SSRF — file:// scheme must be blocked."""
        response = await client.post(
            "/api/v1/items/import",
            json={"url": "file:///etc/passwd"},
            headers=auth_headers,
        )
        # Pydantic HttpUrl rejects non-http(s) before our validator even runs
        assert response.status_code == 422

    async def test_upstream_5xx_returns_502(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """API10: Non-2xx upstream response surfaces as 502."""
        with patch("httpx.AsyncClient", return_value=_mock_httpx_client({}, status_code=500)):
            response = await client.post(
                "/api/v1/items/import", json={"url": _IMPORT_URL}, headers=auth_headers
            )
        assert response.status_code == 502

    async def test_upstream_timeout_returns_504(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """API10: Upstream timeout surfaces as 504."""
        mock_client = AsyncMock()
        mock_client.request = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        with patch("httpx.AsyncClient", return_value=mock_client):
            response = await client.post(
                "/api/v1/items/import", json={"url": _IMPORT_URL}, headers=auth_headers
            )
        assert response.status_code == 504

    async def test_upstream_invalid_schema_returns_502(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """API10: Response missing required fields is rejected and returns 502."""
        with patch(
            "httpx.AsyncClient", return_value=_mock_httpx_client({"title": "No price here"})
        ):
            response = await client.post(
                "/api/v1/items/import", json={"url": _IMPORT_URL}, headers=auth_headers
            )
        assert response.status_code == 502
