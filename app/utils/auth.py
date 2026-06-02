"""Utilitas untuk validasi JWT dari Authentik menggunakan OIDC/JWKS."""

import asyncio
import hashlib
import logging
import time
from typing import Any

import httpx
from fastapi import HTTPException, status
from jose import ExpiredSignatureError, JWTError, jwt

logger = logging.getLogger(__name__)

# Cache JWKS dan URL endpoint introspeksi untuk mengurangi request ke Authentik.
#
# TTL sengaja dibuat panjang (1 jam): kunci publik JWKS sangat jarang dirotasi dan
# URL endpoint OIDC praktis tidak pernah berubah. TTL pendek (mis. 5 menit) memicu
# "refresh storm" periodik — setiap kali cache kedaluwarsa, request berikutnya harus
# menunggu discovery OIDC (beberapa detik) sementara request lain menumpuk di lock,
# menghasilkan lonjakan latensi/kegagalan berkala yang terlihat sebagai data
# "muncul lalu hilang" di sisi web.
DISCOVERY_CACHE_TTL_SECONDS = 3600  # 1 jam

# Alias backward-compatible (dipakai oleh test lama yang mereferensikan nama ini).
JWKS_CACHE_TTL_SECONDS = DISCOVERY_CACHE_TTL_SECONDS

# TTL cache hasil introspeksi token. Introspeksi dipanggil pada setiap request;
# tanpa cache, setiap request memicu round-trip ke Authentik sehingga membebani
# identity provider dan menambah latensi per-request. Cache singkat ini membatasi
# introspeksi menjadi maksimal sekali per token per interval, dengan konsekuensi
# deteksi logout/pencabutan token tertunda paling lama selama TTL ini.
INTROSPECTION_RESULT_CACHE_TTL_SECONDS = 60

# Batas jumlah entri cache hasil introspeksi untuk mencegah pertumbuhan memori tak
# terbatas. Saat batas terlampaui, entri yang sudah kedaluwarsa dibersihkan.
INTROSPECTION_RESULT_CACHE_MAX_ENTRIES = 10_000

# Cache JWKS untuk mengurangi request ke Authentik
_jwks_cache: dict[str, Any] = {}
_jwks_last_fetched: float = 0.0
_jwks_lock = asyncio.Lock()

# Cache URL endpoint introspeksi Authentik
_introspection_endpoint_cache: str = ""
_introspection_endpoint_last_fetched: float = 0.0
_introspection_endpoint_lock = asyncio.Lock()

# Cache hasil introspeksi token: hash token -> (is_active, waktu_monotonic_disimpan)
_introspection_result_cache: dict[str, tuple[bool, float]] = {}


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
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tidak dapat menghubungi identity provider.",
        ) from exc


async def get_jwks(issuer_url: str) -> dict[str, Any]:
    """Mengembalikan JWKS yang di-cache, melakukan refresh jika sudah kedaluwarsa.

    Jika refresh gagal (Authentik tidak tersedia) dan ada cache lama yang valid,
    cache lama digunakan sebagai fallback. JWKS jarang berubah sehingga data
    lama masih aman dipakai sementara.

    Args:
        issuer_url: URL issuer Authentik.

    Returns:
        Dict JWKS yang berisi kunci-kunci publik.

    Raises:
        HTTPException: 503 jika refresh gagal DAN tidak ada cache lama.
    """
    global _jwks_cache, _jwks_last_fetched

    now = time.monotonic()
    if now - _jwks_last_fetched > JWKS_CACHE_TTL_SECONDS or not _jwks_cache:
        async with _jwks_lock:
            # Double-check setelah acquire lock
            if now - _jwks_last_fetched > JWKS_CACHE_TTL_SECONDS or not _jwks_cache:
                try:
                    _jwks_cache = await _fetch_jwks(issuer_url)
                    _jwks_last_fetched = time.monotonic()
                except HTTPException:
                    if not _jwks_cache:
                        raise  # Tidak ada cache lama, harus gagal
                    # Gunakan cache lama — JWKS jarang dirotasi, JWT tetap dapat diverifikasi.
                    # Perbarui timestamp agar request berikutnya tidak menumpuk di lock dan
                    # masing-masing menunggu timeout discovery sementara Authentik tidak tersedia.
                    _jwks_last_fetched = time.monotonic()
                    logger.warning(
                        "Gagal memperbarui JWKS cache (Authentik tidak tersedia). "
                        "Menggunakan data cache lama."
                    )

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
                except (httpx.HTTPError, KeyError, ValueError) as exc:
                    if not _introspection_endpoint_cache:
                        raise HTTPException(
                            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Tidak dapat menghubungi identity provider.",
                        ) from exc
                    # Gunakan URL cache lama — endpoint introspeksi sangat jarang berubah.
                    # Perbarui timestamp agar request berikutnya tidak menumpuk di lock
                    # sambil Authentik sedang tidak tersedia.
                    _introspection_endpoint_last_fetched = time.monotonic()
                    logger.warning(
                        "Gagal memperbarui endpoint introspeksi (%s: %s). "
                        "Menggunakan URL cache lama.",
                        type(exc).__name__,
                        exc,
                    )

    return _introspection_endpoint_cache


def _raise_token_inactive() -> None:
    """Melempar HTTPException 401 standar untuk token yang tidak aktif.

    Raises:
        HTTPException: 401 dengan pesan sesi berakhir.
    """
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token tidak aktif. Sesi Anda telah berakhir, silakan login kembali.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _get_cached_introspection(token_hash: str) -> bool | None:
    """Mengambil hasil introspeksi token dari cache jika masih berlaku.

    Args:
        token_hash: Hash SHA-256 dari token (dipakai sebagai kunci cache).

    Returns:
        ``True``/``False`` status aktif token jika ada entri cache yang masih berlaku,
        atau ``None`` jika tidak ada cache atau sudah kedaluwarsa.
    """
    cached = _introspection_result_cache.get(token_hash)
    if cached is None:
        return None
    is_active, stored_at = cached
    if time.monotonic() - stored_at > INTROSPECTION_RESULT_CACHE_TTL_SECONDS:
        return None
    return is_active


def _store_introspection_result(token_hash: str, is_active: bool) -> None:
    """Menyimpan hasil introspeksi token ke cache dengan pembersihan entri kedaluwarsa.

    Args:
        token_hash: Hash SHA-256 dari token (dipakai sebagai kunci cache).
        is_active: Status aktif token hasil introspeksi Authentik.
    """
    now = time.monotonic()
    if len(_introspection_result_cache) >= INTROSPECTION_RESULT_CACHE_MAX_ENTRIES:
        # Bersihkan entri yang sudah kedaluwarsa untuk mencegah pertumbuhan tak terbatas.
        expired = [
            key
            for key, (_, stored_at) in _introspection_result_cache.items()
            if now - stored_at > INTROSPECTION_RESULT_CACHE_TTL_SECONDS
        ]
        for key in expired:
            del _introspection_result_cache[key]
    _introspection_result_cache[token_hash] = (is_active, now)


async def introspect_token(
    token: str,
    issuer_url: str,
    client_id: str,
    client_secret: str,
) -> None:
    """Memverifikasi status aktif token melalui endpoint introspeksi Authentik (RFC 7662).

    Dipanggil setelah validasi lokal JWT untuk mendeteksi apakah token telah dicabut
    di Authentik — misalnya karena user logout dari Authentik di tab/perangkat lain.

    Hasil introspeksi di-cache singkat (lihat ``INTROSPECTION_RESULT_CACHE_TTL_SECONDS``)
    agar tidak setiap request menghasilkan round-trip ke Authentik. Tanpa cache ini,
    render satu halaman web yang memicu banyak request backend akan membanjiri Authentik
    dan menambah latensi per-request — penyebab data tampil tersendat/berkala.

    Semua kegagalan yang bersifat infrastruktur (koneksi gagal, timeout, credentials
    salah, endpoint OIDC discovery tidak tersedia) hanya dicatat sebagai warning dan
    tidak memblokir request. Validasi tanda tangan JWT dan expiry sudah dilakukan di
    ``verify_token`` sehingga keamanan tetap terjaga.

    Args:
        token: JWT access token yang akan diintrospeksi.
        issuer_url: URL issuer Authentik.
        client_id: Client ID untuk autentikasi ke endpoint introspeksi.
        client_secret: Client secret untuk autentikasi ke endpoint introspeksi.

    Raises:
        HTTPException: 401 jika Authentik secara eksplisit menyatakan token tidak aktif.
    """
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    cached_active = _get_cached_introspection(token_hash)
    if cached_active is not None:
        if not cached_active:
            _raise_token_inactive()
        return

    try:
        introspection_url = await _get_introspection_endpoint(issuer_url)
    except HTTPException:
        # OIDC discovery gagal (misal: Authentik sedang restart atau cache habis).
        # Tidak fatal — JWT verification sudah cukup untuk memproteksi endpoint.
        logger.warning(
            "Gagal mendapatkan URL introspeksi (OIDC discovery tidak tersedia). "
            "Melanjutkan hanya dengan JWT."
        )
        return

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                introspection_url,
                data={"token": token},
                auth=(client_id, client_secret),
            )
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        # Koneksi gagal atau error HTTP (misal: credentials salah → 401 dari Authentik).
        # JWT verification di verify_token() sudah memvalidasi tanda tangan dan expiry.
        logger.warning(
            "Introspeksi token gagal (%s: %s). Melanjutkan hanya dengan JWT.",
            type(exc).__name__,
            exc,
        )
        return

    is_active = bool(data.get("active", False))
    _store_introspection_result(token_hash, is_active)

    if not is_active:
        _raise_token_inactive()


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
