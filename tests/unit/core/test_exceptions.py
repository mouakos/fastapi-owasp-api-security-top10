"""Unit tests for custom application exception classes."""

from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BadGatewayError,
    ConflictError,
    GatewayTimeoutError,
    NotFoundError,
    ServiceUnavailableError,
    ValidationError,
)


def test_not_found_error_has_correct_status() -> None:
    err = NotFoundError("User", "some-id")
    assert err.status_code == 404
    assert err.error_code == "NOT_FOUND"
    assert "some-id" in err.message


def test_not_found_error_custom_message() -> None:
    err = NotFoundError("Item", "abc", message="custom message")
    assert err.message == "custom message"


def test_validation_error_with_value() -> None:
    err = ValidationError("email", "invalid format", value="bad@")
    assert err.status_code == 422
    assert err.details["value"] == "bad@"


def test_validation_error_without_value() -> None:
    err = ValidationError("field", "required")
    assert err.details["value"] is None


def test_authentication_error_default_message() -> None:
    err = AuthenticationError()
    assert err.status_code == 401
    assert err.message == "Authentication required"


def test_authorization_error() -> None:
    err = AuthorizationError("delete", "Item")
    assert err.status_code == 403
    assert "delete" in err.message
    assert err.details["action"] == "delete"


def test_conflict_error_default_message() -> None:
    err = ConflictError("User")
    assert err.status_code == 409
    assert err.error_code == "RESOURCE_CONFLICT"


def test_conflict_error_custom_message() -> None:
    err = ConflictError("User", message="email already in use")
    assert err.message == "email already in use"


def test_service_unavailable_error_default_message() -> None:
    err = ServiceUnavailableError("PaymentAPI")
    assert err.status_code == 503
    assert err.error_code == "SERVICE_UNAVAILABLE"
    assert "PaymentAPI" in err.message
    assert err.details["service"] == "PaymentAPI"


def test_service_unavailable_error_custom_message() -> None:
    err = ServiceUnavailableError("EmailService", message="temporarily down")
    assert err.message == "temporarily down"


def test_bad_gateway_error_default_message() -> None:
    err = BadGatewayError("InventoryAPI")
    assert err.status_code == 502
    assert err.error_code == "BAD_GATEWAY"
    assert "InventoryAPI" in err.message
    assert err.details["service"] == "InventoryAPI"


def test_bad_gateway_error_custom_message() -> None:
    err = BadGatewayError("InventoryAPI", message="invalid response")
    assert err.message == "invalid response"


def test_gateway_timeout_error_default_message() -> None:
    err = GatewayTimeoutError("ShippingAPI")
    assert err.status_code == 504
    assert err.error_code == "GATEWAY_TIMEOUT"
    assert "ShippingAPI" in err.message
    assert err.details["service"] == "ShippingAPI"


def test_gateway_timeout_error_custom_message() -> None:
    err = GatewayTimeoutError("ShippingAPI", message="timed out after 30s")
    assert err.message == "timed out after 30s"
