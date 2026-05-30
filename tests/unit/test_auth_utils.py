"""Unit test untuk utilitas autentikasi JWT."""

from unittest.mock import AsyncMock, patch

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
