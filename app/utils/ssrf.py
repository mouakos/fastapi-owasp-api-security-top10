"""SSRF (Server-Side Request Forgery) protection utility.

API7: Before the application makes any outbound HTTP request based on a
user-supplied URL, that URL must pass this validation.  The checks below
prevent attackers from redirecting server-side requests to:
  - Internal services (RFC 1918 private ranges, loopback)
  - Cloud metadata endpoints (169.254.169.254)
  - Non-HTTP schemes that could trigger unintended protocol handlers
"""

import ipaddress
import re
import socket
from urllib.parse import urlparse

from app.core.exceptions import ValidationError

# ---------------------------------------------------------------------------
# API7: Only HTTP and HTTPS are permitted outbound schemes.
# ---------------------------------------------------------------------------
_ALLOWED_SCHEMES: frozenset[str] = frozenset({"http", "https"})

# ---------------------------------------------------------------------------
# API7: Block well-known loopback/internal hostnames by name before DNS lookup.
#       Catches case-insensitive variants (LOCALHOST, LocalHost), common aliases
#       (localhost.localdomain, *.local), and wildcard-DNS services that resolve
#       to 127.0.0.1 (localtest.me, nip.io, sslip.io tricks).
#       This is defence-in-depth: the IP-range check below is the primary gate,
#       but blocking at the hostname level avoids the DNS round-trip entirely.
# ---------------------------------------------------------------------------
_LOCALHOST_RE: re.Pattern[str] = re.compile(
    r"""
    ^(
        localhost                   # plain localhost
        | localhost\..*             # localhost.localdomain, localhost.local, …
        | .*\.local$                # mDNS .local TLD
        | localtest\.me             # wildcard-DNS → 127.0.0.1
        | .*\.localtest\.me$        # sub.localtest.me
        | .*\.nip\.io$              # 192.168.x.x.nip.io → resolves to that IP
        | .*\.sslip\.io$            # similar wildcard-DNS service
        | metadata\.google\.internal  # GCP metadata endpoint by name
    )$
    """,
    re.IGNORECASE | re.VERBOSE,
)

# ---------------------------------------------------------------------------
# API7: Network ranges that must never be reachable via user-supplied URLs.
#       Covers loopback, RFC 1918 private, link-local (incl. cloud metadata),
#       and IPv6 equivalents.
# ---------------------------------------------------------------------------
_BLOCKED_NETWORKS: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = [
    ipaddress.ip_network("127.0.0.0/8"),  # IPv4 loopback
    ipaddress.ip_network("10.0.0.0/8"),  # RFC 1918 class A
    ipaddress.ip_network("172.16.0.0/12"),  # RFC 1918 class B
    ipaddress.ip_network("192.168.0.0/16"),  # RFC 1918 class C
    ipaddress.ip_network("169.254.0.0/16"),  # link-local / cloud metadata (AWS, GCP, Azure)
    ipaddress.ip_network("0.0.0.0/8"),  # "this" network
    ipaddress.ip_network("100.64.0.0/10"),  # shared address space (RFC 6598)
    ipaddress.ip_network("::1/128"),  # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),  # IPv6 unique local (ULA)
    ipaddress.ip_network("fe80::/10"),  # IPv6 link-local
]


def validate_ssrf(url: str) -> str:
    """Validate a user-supplied URL against SSRF attack vectors.

    Performs four checks in order:
      1. Scheme must be http or https.
      2. Hostname must be present and must not match known loopback/internal names.
      3. Hostname must be resolvable.
      4. Resolved IP must not fall within any blocked network range.

    Args:
        url: The raw URL string provided by the client.

    Returns:
        The original URL string if all checks pass.

    Raises:
        ValidationError: If the URL fails any SSRF safety check.
    """
    parsed = urlparse(url)

    # API7: Reject non-HTTP schemes (file://, gopher://, ftp://, etc.)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise ValidationError(
            "url",
            f"Scheme '{parsed.scheme}' is not allowed; only http and https are permitted",
        )

    hostname = parsed.hostname
    if not hostname:
        raise ValidationError("url", "URL must contain a valid hostname")

    # API7: Reject well-known loopback/internal hostnames before DNS resolution.
    if _LOCALHOST_RE.match(hostname):
        raise ValidationError(
            "url",
            f"Hostname '{hostname}' is not allowed",
        )

    # API7: Resolve hostname to IP and reject if it maps to a restricted range.
    #       DNS rebinding attacks are mitigated by resolving at validation time.
    try:
        addr_infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise ValidationError("url", f"Could not resolve hostname '{hostname}'") from exc

    for addr_info in addr_infos:
        ip_str = addr_info[4][0]
        try:
            ip_obj = ipaddress.ip_address(ip_str)
        except ValueError as exc:
            raise ValidationError("url", f"Invalid IP address returned for '{hostname}'") from exc

        for network in _BLOCKED_NETWORKS:
            if ip_obj in network:
                raise ValidationError(
                    "url",
                    "URL resolves to a restricted network address and cannot be fetched",
                )

    return url
