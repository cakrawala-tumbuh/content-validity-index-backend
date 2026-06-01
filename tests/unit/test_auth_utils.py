"""Unit test untuk utilitas autentikasi JWT."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


class TestVerifyToken:
    """Kumpulan test untuk fungsi verify_token."""

    @pytest.mark.asyncio
    async def test_token_valid_mengembalikan_claims(self) -> None:
        """verify_token harus mengembalikan claims jika token valid."""
        mock_claims = {"sub": "user-123", "email": "test@example.com", "groups": ["cvi-expert"]}

        with (
            patch("app.utils.auth.get_jwks", new_callable=AsyncMock) as mock_jwks,
            patch("app.utils.auth.jwt.decode") as mock_decode,
        ):
            mock_jwks.return_value = {"keys": []}
            mock_decode.return_value = mock_claims

            from app.utils.auth import verify_token

            result = await verify_token("valid.jwt.token", "https://auth.example.com")
            assert result == mock_claims

    @pytest.mark.asyncio
    async def test_token_kedaluwarsa_raise_401(self) -> None:
        """verify_token harus raise HTTPException 401 jika token kedaluwarsa."""
        from jose import ExpiredSignatureError

        with (
            patch("app.utils.auth.get_jwks", new_callable=AsyncMock) as mock_jwks,
            patch("app.utils.auth.jwt.decode") as mock_decode,
        ):
            mock_jwks.return_value = {"keys": []}
            mock_decode.side_effect = ExpiredSignatureError("expired")

            from app.utils.auth import verify_token

            with pytest.raises(HTTPException) as exc_info:
                await verify_token("expired.jwt.token", "https://auth.example.com")
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_token_tidak_valid_raise_401(self) -> None:
        """verify_token harus raise HTTPException 401 jika token tidak valid."""
        from jose import JWTError

        with (
            patch("app.utils.auth.get_jwks", new_callable=AsyncMock) as mock_jwks,
            patch("app.utils.auth.jwt.decode") as mock_decode,
        ):
            mock_jwks.return_value = {"keys": []}
            mock_decode.side_effect = JWTError("invalid signature")

            from app.utils.auth import verify_token

            with pytest.raises(HTTPException) as exc_info:
                await verify_token("invalid.jwt.token", "https://auth.example.com")
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_jwks_fetch_gagal_raise_503(self) -> None:
        """verify_token harus raise HTTPException 503 jika JWKS tidak bisa diambil."""
        from fastapi import HTTPException

        with (
            patch("app.utils.auth._fetch_jwks", new_callable=AsyncMock) as mock_fetch,
            patch("app.utils.auth._jwks_last_fetched", 0.0),
            patch("app.utils.auth._jwks_cache", {}),
        ):
            mock_fetch.side_effect = HTTPException(status_code=503, detail="tidak bisa connect")

            from app.utils.auth import get_jwks

            with pytest.raises(HTTPException) as exc_info:
                await get_jwks("https://auth.example.com")
            assert exc_info.value.status_code == 503


class TestIntrospectToken:
    """Kumpulan test untuk fungsi introspect_token (validasi status aktif token di Authentik)."""

    @pytest.mark.asyncio
    async def test_token_aktif_tidak_raise(self) -> None:
        """introspect_token tidak boleh raise exception jika Authentik menyatakan token aktif."""
        with (
            patch(
                "app.utils.auth._get_introspection_endpoint", new_callable=AsyncMock
            ) as mock_ep,
            patch("app.utils.auth.httpx.AsyncClient") as MockClient,
        ):
            mock_ep.return_value = "https://auth.example.com/introspect"
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"active": True, "sub": "user-123"}
            mock_resp.raise_for_status.return_value = None
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_resp)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

            from app.utils.auth import introspect_token

            await introspect_token(
                "valid.active.token", "https://auth.example.com", "client_id", "secret"
            )

    @pytest.mark.asyncio
    async def test_token_tidak_aktif_raise_401(self) -> None:
        """introspect_token harus raise 401 jika Authentik menyatakan token tidak aktif."""
        with (
            patch(
                "app.utils.auth._get_introspection_endpoint", new_callable=AsyncMock
            ) as mock_ep,
            patch("app.utils.auth.httpx.AsyncClient") as MockClient,
        ):
            mock_ep.return_value = "https://auth.example.com/introspect"
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"active": False}
            mock_resp.raise_for_status.return_value = None
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_resp)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

            from app.utils.auth import introspect_token

            with pytest.raises(HTTPException) as exc_info:
                await introspect_token(
                    "revoked.token", "https://auth.example.com", "client_id", "secret"
                )
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_introspeksi_gagal_raise_503(self) -> None:
        """introspect_token harus raise 503 jika endpoint introspeksi tidak dapat dihubungi."""
        import httpx as httpx_module

        with (
            patch(
                "app.utils.auth._get_introspection_endpoint", new_callable=AsyncMock
            ) as mock_ep,
            patch("app.utils.auth.httpx.AsyncClient") as MockClient,
        ):
            mock_ep.return_value = "https://auth.example.com/introspect"
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(
                side_effect=httpx_module.ConnectError("Connection refused")
            )
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

            from app.utils.auth import introspect_token

            with pytest.raises(HTTPException) as exc_info:
                await introspect_token(
                    "some.token", "https://auth.example.com", "client_id", "secret"
                )
            assert exc_info.value.status_code == 503


class TestSkenarioBugLogoutAuthentik:
    """
    Simulasi bug: user masih bisa akses CVI setelah logout dari Authentik.

    Alur bug:
    1. User login ke Authentik → dapat JWT access token
    2. User logout dari Authentik (session Authentik berakhir, token dicabut di Authentik)
    3. Token masih valid secara kriptografi (belum expired, signature OK)
    4. Bug lama: CVI menerima token → user tetap bisa akses CVI
    5. Fix: CVI memanggil introspeksi Authentik → token ditolak dengan 401
    """

    @pytest.mark.asyncio
    async def test_token_valid_lokal_tapi_dicabut_di_authentik_ditolak(self) -> None:
        """Token valid secara lokal tapi dicabut di Authentik harus ditolak dengan 401.

        Ini mereproduksi skenario: login CVI → logout Authentik → masih bisa akses CVI.
        """
        mock_claims = {"sub": "user-123", "email": "user@example.com", "groups": []}

        with (
            patch("app.utils.auth.get_jwks", new_callable=AsyncMock) as mock_jwks,
            patch("app.utils.auth.jwt.decode") as mock_decode,
            patch(
                "app.utils.auth._get_introspection_endpoint", new_callable=AsyncMock
            ) as mock_ep,
            patch("app.utils.auth.httpx.AsyncClient") as MockClient,
        ):
            # Token valid secara kriptografi (belum expired, signature OK)
            mock_jwks.return_value = {"keys": []}
            mock_decode.return_value = mock_claims

            # Authentik menyatakan token sudah tidak aktif (user telah logout Authentik)
            mock_ep.return_value = "https://auth.example.com/introspect"
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"active": False}
            mock_resp.raise_for_status.return_value = None
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_resp)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

            from app.utils.auth import introspect_token, verify_token

            # Validasi lokal berhasil — inilah yang menyebabkan bug sebelumnya
            claims = await verify_token("valid.but.revoked.token", "https://auth.example.com")
            assert claims == mock_claims

            # Introspeksi Authentik harus menolak token tersebut
            with pytest.raises(HTTPException) as exc_info:
                await introspect_token(
                    "valid.but.revoked.token",
                    "https://auth.example.com",
                    "client_id",
                    "client_secret",
                )
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_token_valid_dan_aktif_di_authentik_diterima(self) -> None:
        """Token valid secara lokal DAN aktif di Authentik harus diterima tanpa exception."""
        mock_claims = {"sub": "user-123", "email": "user@example.com", "groups": []}

        with (
            patch("app.utils.auth.get_jwks", new_callable=AsyncMock) as mock_jwks,
            patch("app.utils.auth.jwt.decode") as mock_decode,
            patch(
                "app.utils.auth._get_introspection_endpoint", new_callable=AsyncMock
            ) as mock_ep,
            patch("app.utils.auth.httpx.AsyncClient") as MockClient,
        ):
            mock_jwks.return_value = {"keys": []}
            mock_decode.return_value = mock_claims

            mock_ep.return_value = "https://auth.example.com/introspect"
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"active": True, "sub": "user-123"}
            mock_resp.raise_for_status.return_value = None
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_resp)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

            from app.utils.auth import introspect_token, verify_token

            claims = await verify_token("valid.active.token", "https://auth.example.com")
            assert claims == mock_claims

            # Tidak boleh raise exception
            await introspect_token(
                "valid.active.token",
                "https://auth.example.com",
                "client_id",
                "client_secret",
            )
