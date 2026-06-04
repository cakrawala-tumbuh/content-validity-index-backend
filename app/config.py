"""Konfigurasi aplikasi melalui environment variables."""

import json
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Pengaturan aplikasi yang dibaca dari environment variables.

    Semua nilai sensitif wajib dikonfigurasi via environment variable,
    tidak boleh di-hardcode di dalam kode.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./cvi.db"

    # Authentik OIDC
    AUTHENTIK_ISSUER_URL: str = "https://authentik.example.com/application/o/cvi/"
    AUTHENTIK_CLIENT_ID: str = ""
    AUTHENTIK_CLIENT_SECRET: str = ""
    AUTHENTIK_ADMIN_GROUP: str = "cvi-admin"
    AUTHENTIK_EXPERT_GROUP: str = "cvi-expert"

    # Aplikasi
    APP_ENV: str = "development"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Reverse proxy — daftar IP yang dipercaya mengirim header X-Forwarded-*.
    # Di belakang Traefik (TLS diterminasi di proxy), backend hanya menerima HTTP
    # sehingga perlu menghormati X-Forwarded-Proto agar redirect memakai skema https
    # dan tidak menstrip header Authorization saat di-follow. Default "*" aman karena
    # backend hanya dapat dijangkau melalui reverse proxy pada jaringan internal.
    FORWARDED_ALLOW_IPS: str = "*"

    def model_post_init(self, __context: object) -> None:
        """Normalisasi `CORS_ORIGINS` setelah model selesai diinisialisasi.

        Hook bawaan Pydantic yang dipanggil otomatis sesudah validasi. Bila
        `CORS_ORIGINS` diterima sebagai JSON string (mis. dari environment
        variable), nilainya di-parse menjadi list.

        Args:
            __context: Konteks yang disuplai Pydantic; tidak digunakan di sini.
        """
        if isinstance(self.CORS_ORIGINS, str):
            object.__setattr__(self, "CORS_ORIGINS", json.loads(self.CORS_ORIGINS))


@lru_cache
def get_settings() -> Settings:
    """Mengembalikan instance Settings yang di-cache (singleton).

    Returns:
        Instance Settings yang sudah dikonfigurasi.
    """
    return Settings()
