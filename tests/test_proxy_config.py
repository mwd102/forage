from app.browser import BrowserPool
from app.config import DEFAULTS, BrowserConfig, ForageConfig, deep_merge


def test_proxy_credentials_come_from_environment(monkeypatch):
    monkeypatch.setenv("FORAGE_PROXY_SERVER", "http://proxy.example:8000")
    monkeypatch.setenv("FORAGE_PROXY_USERNAME", "agent")
    monkeypatch.setenv("FORAGE_PROXY_PASSWORD", "secret")
    data = deep_merge(DEFAULTS, {"proxy": {"enabled": True, "mode": "fallback"}})

    config = ForageConfig.from_dict(data, "test.yaml")
    config.validate()

    assert config.proxy.server == "http://proxy.example:8000"
    assert config.proxy.username == "agent"
    assert config.proxy.password == "secret"


def test_browser_translates_proxy_for_playwright():
    class Proxy:
        server = "http://proxy.example:8000"
        username = "agent"
        password = "secret"

    pool = BrowserPool(BrowserConfig(), proxy=Proxy())

    assert pool._playwright_proxy() == {
        "server": "http://proxy.example:8000",
        "username": "agent",
        "password": "secret",
    }
