"""Unit tests for the safe external HTTP client utility (API10)."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from pydantic import BaseModel

from app.core.exceptions import BadGatewayError, GatewayTimeoutError, ServiceUnavailableError
from app.utils.http_client import _MAX_RESPONSE_BYTES, fetch_external


class _SampleSchema(BaseModel):
    title: str
    price: float


def _make_response(
    status_code: int = 200,
    json_data: dict | None = None,
    content: bytes | None = None,
) -> MagicMock:
    """Build a minimal mock httpx.Response."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.content = content if content is not None else b'{"title":"Widget","price":1.99}'
    response.json.return_value = (
        json_data if json_data is not None else {"title": "Widget", "price": 1.99}
    )
    if status_code >= 400:
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message=f"HTTP {status_code}",
            request=MagicMock(),
            response=response,
        )
    else:
        response.raise_for_status.return_value = None
    return response


def _make_client(response: MagicMock) -> MagicMock:
    """Wrap a mock response in a mock AsyncClient context manager."""
    mock_client = AsyncMock()
    mock_client.request = AsyncMock(return_value=response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return mock_client


class TestFetchExternalSuccess:
    """API10: Valid external responses are parsed through the schema."""

    async def test_returns_validated_model(self) -> None:
        response = _make_response(json_data={"title": "Widget", "price": 1.99})
        with patch("httpx.AsyncClient", return_value=_make_client(response)):
            result = await fetch_external("https://example.com/item", _SampleSchema)
        assert isinstance(result, _SampleSchema)
        assert result.title == "Widget"
        assert result.price == 1.99

    async def test_extra_fields_in_response_are_ignored(self) -> None:
        """API10: Unknown fields from the upstream are discarded."""
        response = _make_response(
            json_data={"title": "Widget", "price": 1.99, "unexpected_field": "ignored"}
        )
        with patch("httpx.AsyncClient", return_value=_make_client(response)):
            result = await fetch_external("https://example.com/item", _SampleSchema)
        assert result.title == "Widget"


class TestFetchExternalTimeout:
    """API10: Timeouts raise GatewayTimeoutError (504)."""

    async def test_timeout_raises_gateway_timeout(self) -> None:
        mock_client = AsyncMock()
        mock_client.request = AsyncMock(side_effect=httpx.TimeoutException("timed out"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("httpx.AsyncClient", return_value=mock_client),
            pytest.raises(GatewayTimeoutError) as exc_info,
        ):
            await fetch_external("https://example.com/item", _SampleSchema, service_name="test-svc")
        assert exc_info.value.status_code == 504


class TestFetchExternalHTTPErrors:
    """API10: Non-2xx responses raise BadGatewayError (502)."""

    @pytest.mark.parametrize("status_code", [400, 401, 403, 404, 500, 503])
    async def test_non_2xx_raises_bad_gateway(self, status_code: int) -> None:
        response = _make_response(status_code=status_code)
        with (
            patch("httpx.AsyncClient", return_value=_make_client(response)),
            pytest.raises(BadGatewayError) as exc_info,
        ):
            await fetch_external("https://example.com/item", _SampleSchema)
        assert exc_info.value.status_code == 502


class TestFetchExternalNetworkError:
    """API10: Network errors raise ServiceUnavailableError (503)."""

    async def test_request_error_raises_service_unavailable(self) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.request = AsyncMock(
            side_effect=httpx.RequestError("connection refused", request=MagicMock())
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("httpx.AsyncClient", return_value=mock_client),
            pytest.raises(ServiceUnavailableError) as exc_info,
        ):
            await fetch_external("https://example.com/item", _SampleSchema)
        assert exc_info.value.status_code == 503


class TestFetchExternalOversizedResponse:
    """API10: Payloads exceeding the size cap raise BadGatewayError (502)."""

    async def test_oversized_payload_raises_bad_gateway(self) -> None:
        oversized = b"x" * (_MAX_RESPONSE_BYTES + 1)
        response = _make_response(content=oversized)
        with (
            patch("httpx.AsyncClient", return_value=_make_client(response)),
            pytest.raises(BadGatewayError) as exc_info,
        ):
            await fetch_external("https://example.com/item", _SampleSchema)
        assert exc_info.value.status_code == 502


class TestFetchExternalSchemaValidation:
    """API10: Responses not matching the schema raise BadGatewayError (502)."""

    async def test_missing_required_field_raises_bad_gateway(self) -> None:
        response = _make_response(json_data={"title": "Widget"})  # price missing
        with (
            patch("httpx.AsyncClient", return_value=_make_client(response)),
            pytest.raises(BadGatewayError) as exc_info,
        ):
            await fetch_external("https://example.com/item", _SampleSchema)
        assert exc_info.value.status_code == 502

    async def test_wrong_field_type_raises_bad_gateway(self) -> None:
        response = _make_response(json_data={"title": "Widget", "price": "not-a-number"})
        with (
            patch("httpx.AsyncClient", return_value=_make_client(response)),
            pytest.raises(BadGatewayError) as exc_info,
        ):
            await fetch_external("https://example.com/item", _SampleSchema)
        assert exc_info.value.status_code == 502
