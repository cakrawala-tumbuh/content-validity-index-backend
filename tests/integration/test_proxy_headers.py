"""Integration test untuk ProxyHeadersMiddleware di belakang reverse proxy.

Memverifikasi bahwa backend menghormati header X-Forwarded-Proto dari Traefik
sehingga redirect trailing-slash memakai skema https. Tanpa ini, FastAPI membuat
redirect ke http:// yang menstrip header Authorization saat klien mengikutinya.
"""

import pytest
from httpx import AsyncClient


class TestProxyHeadersRedirect:
    """Kumpulan test untuk perilaku redirect saat di belakang reverse proxy."""

    @pytest.mark.asyncio
    async def test_redirect_pakai_https_saat_x_forwarded_proto_https(
        self, client: AsyncClient
    ) -> None:
        """Redirect trailing-slash harus memakai https saat X-Forwarded-Proto: https.

        Path tanpa trailing slash memicu redirect 307 ke versi dengan trailing slash.
        Dengan header X-Forwarded-Proto: https, Location harus berskema https agar
        header Authorization tidak distrip saat redirect diikuti.
        """
        resp = await client.get(
            "/api/v1/instruments",
            headers={"X-Forwarded-Proto": "https"},
        )
        assert resp.status_code == 307
        assert resp.headers["location"].startswith("https://")

    @pytest.mark.asyncio
    async def test_redirect_tetap_http_tanpa_x_forwarded_proto(self, client: AsyncClient) -> None:
        """Tanpa header X-Forwarded-Proto, redirect memakai skema asli request (http).

        Memastikan middleware hanya mengubah skema berdasarkan header forwarding,
        bukan memaksa https tanpa indikasi dari reverse proxy.
        """
        resp = await client.get("/api/v1/instruments")
        assert resp.status_code == 307
        assert resp.headers["location"].startswith("http://")
