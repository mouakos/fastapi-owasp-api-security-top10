"""Safe external HTTP client utility.

API10: Consuming external or third-party APIs without validation exposes the
application to unexpected data shapes, injected values, and silent failures.

This module enforces three layers of protection for every outbound call:
  1. Connection and read timeouts — prevents the server from hanging
     indefinitely on a slow or unresponsive upstream service.
  2. Explicit HTTP error handling — non-2xx responses are always surfaced as
     a typed ExternalServiceError rather than silently ignored.
  3. Strict Pydantic validation — the raw JSON response is parsed through a
     caller-supplied schema; any missing or malformed field is rejected before
     the data touches application logic.

Usage example
-------------
Define a schema for the external response:

    class ExchangeRateResponse(BaseModel):
        base: str
        rates: dict[str, float]

Fetch and validate in a service or endpoint:

    result = await fetch_external(
        url="https://api.example.com/rates?base=USD",
        response_model=ExchangeRateResponse,
        service_name="exchange-rate-api",
    )
    usd_to_eur = result.rates["EUR"]

"""

from typing import Any, TypeVar

import httpx
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from app.core.exceptions import (
    BadGatewayError,
    GatewayTimeoutError,
    ServiceUnavailableError,
)

T = TypeVar("T", bound=BaseModel)

# ---------------------------------------------------------------------------
# API10: Conservative timeout — 5 s connect, 10 s total read.
#        Prevents slow-loris or unresponsive upstream from tying up workers.
# ---------------------------------------------------------------------------
_DEFAULT_TIMEOUT = httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=5.0)

# ---------------------------------------------------------------------------
# API10: Cap response size to avoid memory exhaustion from an oversized payload
#        returned by an upstream that the application blindly reads into RAM.
# ---------------------------------------------------------------------------
_MAX_RESPONSE_BYTES = 1 * 1024 * 1024  # 1 MB


async def fetch_external[T: BaseModel](
    url: str,
    response_model: type[T],
    *,
    service_name: str = "external-api",
    method: str = "GET",
    headers: dict[str, str] | None = None,
    payload: dict[str, Any] | None = None,
) -> T:
    """Make an outbound HTTP request and return a validated, typed response.

    Args:
        url: The full URL of the external endpoint to call.
        response_model: A Pydantic model class used to validate the JSON response.
        service_name: Human-readable name of the upstream service, used in error messages.
        method: HTTP method to use (default ``"GET"``).
        headers: Optional additional request headers.
        payload: Optional JSON payload for POST/PUT/PATCH requests.

    Returns:
        An instance of ``response_model`` populated from the validated response.

    Raises:
        GatewayTimeoutError: If the request to the upstream service times out.
        BadGatewayError: If the upstream service returns a non-2xx status or an
                         invalid response that fails schema validation.
        ServiceUnavailableError: If there is a network error or other issue
                                 preventing the request from being made.
    """
    try:
        async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=payload,
            )
            # API10: Always check status — never silently accept error responses
            response.raise_for_status()

            # API10: Guard against oversized payloads from the upstream service
            if len(response.content) > _MAX_RESPONSE_BYTES:
                raise BadGatewayError(
                    service_name,
                    f"Response from '{service_name}' exceeds the maximum allowed size",
                )

    except httpx.TimeoutException as exc:
        raise GatewayTimeoutError(service_name) from exc
    except httpx.HTTPStatusError as exc:
        raise BadGatewayError(
            service_name, message=f"'{service_name}' returned HTTP {exc.response.status_code}"
        ) from exc
    except httpx.RequestError as exc:
        raise ServiceUnavailableError(service_name) from exc

    # API10: Validate the raw JSON through a strict Pydantic schema before
    #        letting any upstream data enter application logic.
    try:
        return response_model.model_validate(response.json())
    except PydanticValidationError as exc:
        raise BadGatewayError(
            service_name,
            f"Response from '{service_name}' did not match the expected schema",
        ) from exc
