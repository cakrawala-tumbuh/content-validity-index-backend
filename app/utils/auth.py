"""Utilitas untuk validasi JWT dari Authentik menggunakan OIDC/JWKS."""

import asyncio
import time
from typing import Any

import httpx
from fastapi import HTTPException, status
from jose import ExpiredSignatureError, JWTError, jwt


# Cache JWKS untuk mengurangi request ke Authentik
_jwks_cache: dict[str, Any] = {}
_jwks_last_fetched: float = 0.0
_jwks_lock = asyncio.Lock()
JWKS_CACHE_TTL_SECONDS = 300  # 5 menit


async def _fetch_jwks(issuer_url: str) -> dict[str, Any]:
    """Mengambil JWKS dari endpoint Authentik.

    Melakukan discovery OIDC terlebih dahulu untuk mendapatkan URL JWKS,
    lalu mengambil kunci publik untuk validasi JWT.

    Args:
        issuer_url: URL issuer Authentik (OIDC well-known endpoint).

    Returns:
        Dict JWKS yang berisi kunci-kunci publik.

    Raises:
        HTTPException: Jika gagal menghubungi Authentik (503).
    """
    well_known_url = issuer_url.rstrip("/") + "/.well-known/openid-configuration"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            oidc_resp = await client.get(well_known_url)
            oidc_resp.raise_for_status()
            jwks_uri: str = oidc_resp.json()["jwks_uri"]

            jwks_resp = await client.get(jwks_uri)
            jwks_resp.raise_for_status()
            return dict(jwks_resp.json())
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tidak dapat menghubungi identity provider.",
        ) from exc


async def get_jwks(issuer_url: str) -> dict[str, Any]:
    """Mengembalikan JWKS yang di-cache, melakukan refresh jika sudah kedaluwarsa.

    Args:
        issuer_url: URL issuer Authentik.

    Returns:
        Dict JWKS yang berisi kunci-kunci publik.
    """
    global _jwks_cache, _jwks_last_fetched

    now = time.monotonic()
    if now - _jwks_last_fetched > JWKS_CACHE_TTL_SECONDS or not _jwks_cache:
        async with _jwks_lock:
            # Double-check setelah acquire lock
            if now - _jwks_last_fetched > JWKS_CACHE_TTL_SECONDS or not _jwks_cache:
                _jwks_cache = await _fetch_jwks(issuer_url)
                _jwks_last_fetched = time.monotonic()

    return _jwks_cache


async def verify_token(token: str, issuer_url: str) -> dict[str, Any]:
    """Memvalidasi JWT dari Authentik dan mengembalikan claims-nya.

    Memverifikasi:
        - Tanda tangan JWT menggunakan kunci publik dari JWKS Authentik.
        - Waktu kedaluwarsa token (exp claim).
        - Issuer token (iss claim) sesuai dengan AUTHENTIK_ISSUER_URL.

    Args:
        token: JWT Bearer token dari header Authorization.
        issuer_url: URL issuer Authentik yang dikonfigurasi.

    Returns:
        Dict berisi semua JWT claims (sub, email, groups, dll.).

    Raises:
        HTTPException: Jika token tidak valid (401) atau kedaluwarsa (401).
    """
    try:
        jwks = await get_jwks(issuer_url)
        payload: dict[str, Any] = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return payload
    except ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token telah kedaluwarsa. Silakan login kembali.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak valid.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
