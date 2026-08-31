import asyncio

from app.config import DEFAULTS, ForageConfig, deep_merge
from app.extract import extract_url


class DirectFailurePool:
    async def render(self, *_args, **_kwargs):
        raise RuntimeError("blocked")

    async def render_with_solver(self, *_args, **_kwargs):
        return "<title>Just a moment</title><p>Checking your browser</p>"


class ProxySuccessPool:
    async def render(self, *_args, **_kwargs):
        return (
            "<html><head><title>Useful page</title></head><body><main>"
            "<h1>Useful page</h1><p>This is enough clean content for an agent "
            "to consume after the direct browser was blocked.</p></main></body></html>"
        )

    async def render_with_solver(self, *_args, **_kwargs):
        return await self.render()


def test_auto_mode_retries_failed_browser_through_proxy():
    data = deep_merge(
        DEFAULTS,
        {
            "extract": {
                "allow_private_networks": True,
                "force_render": True,
                "min_content_chars": 20,
            }
        },
    )
    config = ForageConfig.from_dict(data, "test.yaml")

    result = asyncio.run(
        extract_url(
            config,
            DirectFailurePool(),
            "http://127.0.0.1/article",
            proxy_pool=ProxySuccessPool(),
            proxy_mode="auto",
            force_render=True,
        )
    )

    assert "error" not in result
    assert result["egress"] == "proxy"
    assert result["method"] == "browser+proxy"
    assert result["title"] == "Useful page"
    assert "clean content" in result["content"]
