"""URL validation for requests initiated by agents.

The extractor is intentionally a public-web client, not a network debugging
proxy. Rejecting local destinations avoids accidental access to loopback,
container, and metadata services when an agent follows an untrusted link.
"""

from __future__ import annotations

import asyncio
import ipaddress
import socket
from urllib.parse import urlparse


class UnsafeUrlError(ValueError):
    """Raised when a URL is not an allowed public HTTP(S) destination."""


def _is_public_address(value: str) -> bool:
    address = ipaddress.ip_address(value)
    return bool(address.is_global)


async def validate_public_url(url: str, *, allow_private: bool = False) -> str:
    """Validate the URL scheme, credentials, host, and resolved addresses."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise UnsafeUrlError("Only http and https URLs are supported")
    if parsed.username or parsed.password:
        raise UnsafeUrlError("Credentials in URLs are not supported")
    if not parsed.hostname:
        raise UnsafeUrlError("URL must include a hostname")
    if allow_private:
        return url

    host = parsed.hostname.rstrip(".")
    try:
        if not _is_public_address(host):
            raise UnsafeUrlError("URL resolves to a non-public address")
        return url
    except ValueError:
        pass

    loop = asyncio.get_running_loop()
    try:
        resolved = await loop.getaddrinfo(
            host,
            parsed.port or (443 if parsed.scheme == "https" else 80),
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror as exc:
        raise UnsafeUrlError(f"Could not resolve URL hostname: {host}") from exc

    addresses = {entry[4][0] for entry in resolved}
    if not addresses or any(not _is_public_address(address) for address in addresses):
        raise UnsafeUrlError("URL resolves to a non-public address")
    return url
