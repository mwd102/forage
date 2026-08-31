import asyncio
import socket

import httpx
import pytest

from app.config import DEFAULTS, ForageConfig
from app.extract import _safe_get
from app.url_safety import UnsafeUrlError, validate_public_url


def run(coro):
    return asyncio.run(coro)


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "http://127.0.0.1/",
        "http://[::1]/",
        "http://169.254.169.254/latest/meta-data/",
        "http://user:password@example.com/",
    ],
)
def test_rejects_unsafe_urls(url):
    with pytest.raises(UnsafeUrlError):
        run(validate_public_url(url))


def test_accepts_public_ip():
    assert run(validate_public_url("https://1.1.1.1/")) == "https://1.1.1.1/"


def test_rejects_hostname_with_private_dns_answer(monkeypatch):
    async def fake_getaddrinfo(*_args, **_kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.8", 80))]

    loop = asyncio.new_event_loop()
    monkeypatch.setattr(loop, "getaddrinfo", fake_getaddrinfo)
    asyncio.set_event_loop(loop)
    try:
        with pytest.raises(UnsafeUrlError):
            loop.run_until_complete(validate_public_url("http://example.test/"))
    finally:
        loop.close()
        asyncio.set_event_loop(None)


def test_private_network_opt_out():
    assert run(validate_public_url("http://127.0.0.1/", allow_private=True)) == (
        "http://127.0.0.1/"
    )


def test_redirect_is_validated_before_private_target_is_contacted():
    contacted = []

    def handler(request):
        contacted.append(str(request.url))
        return httpx.Response(302, headers={"location": "http://127.0.0.1/private"})

    config = ForageConfig.from_dict(DEFAULTS, "test.yaml")

    async def request():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            await _safe_get(client, config, "http://93.184.216.34/start")

    with pytest.raises(UnsafeUrlError):
        run(request())
    assert contacted == ["http://93.184.216.34/start"]
