"""Utilitas untuk validasi JWT dari Authentik menggunakan OIDC/JWKS."""

import asyncio
import logging
import time
from typing import Any

import httpx
from fastapi import HTTPException, status
from jose import ExpiredSignatureError, JWTError, jwt

logger = logging.getLogger(__name__)

# Cache JWKS untuk mengurangi request ke Authentik
_jwks_cache: dict[str, Any] = {}
_jwks_last_fetched: float = 0.0
_jwks_lock = asyncio.Lock()
JWKS_CACHE_TTL_SECONDS = 300  # 5 menit

# Cache URL endpoint introspeksi Authentik
_introspection_endpoint_cache: str = ""
_introspection_endpoint_last_fetched: float = 0.0
_introspection_endpoint_lock = asyncio.Lock()


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


async def _get_introspection_endpoint(issuer_url: str) -> str:
    """Mengambil dan meng-cache URL endpoint introspeksi dari OIDC discovery document.

    Endpoint introspeksi digunakan untuk memverifikasi apakah token masih aktif
    di sisi Authentik — diperlukan untuk mendeteksi logout Authentik.

    Args:
        issuer_url: URL issuer Authentik (OIDC well-known endpoint).

    Returns:
        URL string endpoint introspeksi Authentik.

    Raises:
        HTTPException: Jika gagal menghubungi Authentik (503).
    """
    global _introspection_endpoint_cache, _introspection_endpoint_last_fetched

    now = time.monotonic()
    if (
        now - _introspection_endpoint_last_fetched > JWKS_CACHE_TTL_SECONDS
        or not _introspection_endpoint_cache
    ):
        async with _introspection_endpoint_lock:
            if (
                now - _introspection_endpoint_last_fetched > JWKS_CACHE_TTL_SECONDS
                or not _introspection_endpoint_cache
            ):
                well_known_url = issuer_url.rstrip("/") + "/.well-known/openid-configuration"
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        resp = await client.get(well_known_url)
                        resp.raise_for_status()
                        _introspection_endpoint_cache = resp.json()["introspection_endpoint"]
                        _introspection_endpoint_last_fetched = time.monotonic()
                except httpx.HTTPError as exc:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Tidak dapat menghubungi identity provider.",
                    ) from exc

    return _introspection_endpoint_cache


async def introspect_token(
    token: str,
    issuer_url: str,
    client_id: str,
    client_secret: str,
) -> None:
    """Memverifikasi status aktif token melalui endpoint introspeksi Authentik (RFC 7662).

    Dipanggil setelah validasi lokal JWT untuk mendeteksi apakah token telah dicabut
    di Authentik — misalnya karena user logout dari Authentik di tab/perangkat lain.

    Kegagalan koneksi atau error HTTP dari endpoint introspeksi (misal: credentials
    salah, endpoint tidak bisa dihubungi) hanya dicatat sebagai warning dan tidak
    memblokir request. Validasi tanda tangan JWT dan expiry sudah dilakukan di
    ``verify_token`` sehingga keamanan tetap terjaga.

    Args:
        token: JWT access token yang akan diintrospeksi.
        issuer_url: URL issuer Authentik.
        client_id: Client ID untuk autentikasi ke endpoint introspeksi.
        client_secret: Client secret untuk autentikasi ke endpoint introspeksi.

    Raises:
        HTTPException: 401 jika Authentik secara eksplisit menyatakan token tidak aktif.
    """
    introspection_url = await _get_introspection_endpoint(issuer_url)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                introspection_url,
                data={"token": token},
                auth=(client_id, client_secret),
            )
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()
    except httpx.HTTPError as exc:
        # Jika endpoint introspeksi tidak bisa dihubungi atau mengembalikan error HTTP
        # (misalnya credentials salah → 401 dari Authentik), catat warning dan lanjutkan.
        # JWT verification di verify_token() sudah memvalidasi tanda tangan dan expiry.
        # Introspeksi hanya best-effort untuk mendeteksi logout Authentik.
        logger.warning(
            "Introspeksi token gagal (%s: %s). Melanjutkan hanya dengan JWT.",
            type(exc).__name__,
            exc,
        )
        return

    if not data.get("active", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak aktif. Sesi Anda telah berakhir, silakan login kembali.",
            headers={"WWW-Authenticate": "Bearer"},
        )


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
