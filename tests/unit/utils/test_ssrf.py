"""Unit tests for the SSRF validation utility (API7)."""

from unittest.mock import patch

import pytest

from app.core.exceptions import ValidationError
from app.utils.ssrf import validate_ssrf


class TestSchemeValidation:
    """API7: Only http and https schemes are permitted."""

    def test_https_url_is_accepted(self) -> None:
        with patch("socket.getaddrinfo", return_value=[("", "", "", "", ("93.184.216.34", 0))]):
            result = validate_ssrf("https://example.com/data")
        assert result == "https://example.com/data"

    def test_http_url_is_accepted(self) -> None:
        with patch("socket.getaddrinfo", return_value=[("", "", "", "", ("93.184.216.34", 0))]):
            result = validate_ssrf("http://example.com/data")
        assert result == "http://example.com/data"

    def test_file_scheme_is_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Scheme 'file' is not allowed"):
            validate_ssrf("file:///etc/passwd")

    def test_ftp_scheme_is_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Scheme 'ftp' is not allowed"):
            validate_ssrf("ftp://example.com/file")

    def test_gopher_scheme_is_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Scheme 'gopher' is not allowed"):
            validate_ssrf("gopher://example.com")


class TestLocalhostNameBlocking:
    """API7: Well-known loopback/internal hostnames are rejected before DNS lookup."""

    @pytest.mark.parametrize(
        "url",
        [
            "http://localhost/admin",
            "http://LOCALHOST/admin",
            "http://LocalHost/admin",
            "http://localhost.localdomain/",
            "http://myapp.local/",
            "http://localtest.me/",
            "http://sub.localtest.me/",
            "http://192.168.1.1.nip.io/",
            "http://10.0.0.1.sslip.io/",
            "http://metadata.google.internal/computeMetadata/v1/",
        ],
    )
    def test_blocked_hostname_is_rejected(self, url: str) -> None:
        with pytest.raises(ValidationError, match="is not allowed"):
            validate_ssrf(url)


class TestPrivateIPBlocking:
    """API7: URLs resolving to private/reserved IP ranges are rejected."""

    @pytest.mark.parametrize(
        "ip",
        [
            "127.0.0.1",  # loopback
            "127.0.0.2",  # loopback range
            "10.0.0.1",  # RFC 1918 class A
            "172.16.0.1",  # RFC 1918 class B
            "172.31.255.255",  # RFC 1918 class B edge
            "192.168.1.1",  # RFC 1918 class C
            "169.254.169.254",  # cloud metadata (AWS/GCP/Azure)
            "0.0.0.1",  # "this" network
            "100.64.0.1",  # shared address space
        ],
    )
    def test_private_ip_is_rejected(self, ip: str) -> None:
        with (
            patch("socket.getaddrinfo", return_value=[("", "", "", "", (ip, 0))]),
            pytest.raises(ValidationError, match="restricted network address"),
        ):
            validate_ssrf("http://attacker-controlled.example.com/")

    def test_ipv6_loopback_is_rejected(self) -> None:
        with (
            patch("socket.getaddrinfo", return_value=[("", "", "", "", ("::1", 0, 0, 0))]),
            pytest.raises(ValidationError, match="restricted network address"),
        ):
            validate_ssrf("http://attacker-controlled.example.com/")

    def test_public_ip_is_accepted(self) -> None:
        with patch("socket.getaddrinfo", return_value=[("", "", "", "", ("93.184.216.34", 0))]):
            result = validate_ssrf("http://example.com/")
        assert result == "http://example.com/"


class TestDNSResolutionFailure:
    """API7: Unresolvable hostnames are rejected."""

    def test_unresolvable_hostname_raises(self) -> None:
        import socket

        with (
            patch("socket.getaddrinfo", side_effect=socket.gaierror("Name not resolved")),
            pytest.raises(ValidationError, match="Could not resolve hostname"),
        ):
            validate_ssrf("http://does-not-exist.invalid/")


class TestMissingHostname:
    def test_url_without_hostname_raises(self) -> None:
        with pytest.raises(ValidationError, match="valid hostname"):
            validate_ssrf("http:///no-host")
