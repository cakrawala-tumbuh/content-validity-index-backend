"""FastAPI dependencies untuk autentikasi dan otorisasi."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.services.user_service import UserService
from app.utils.auth import introspect_token, verify_token

_security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI dependency untuk mengambil dan memvalidasi user dari JWT.

    Memvalidasi token Bearer, menyinkronkan data user dari Authentik ke
    database lokal, dan mengembalikan instance User yang aktif.

    Args:
        credentials: Credentials HTTP Bearer dari header Authorization.
        db: AsyncSession database dari dependency injection.

    Returns:
        Instance User yang terautentikasi.

    Raises:
        HTTPException: Jika token tidak valid (401) atau akun tidak aktif (403).
    """
    settings = get_settings()
    claims = await verify_token(credentials.credentials, settings.AUTHENTIK_ISSUER_URL)
    await introspect_token(
        credentials.credentials,
        settings.AUTHENTIK_ISSUER_URL,
        settings.AUTHENTIK_CLIENT_ID,
        settings.AUTHENTIK_CLIENT_SECRET,
    )
    user_service = UserService(db)
    user = await user_service.sync_from_claims(
        claims=claims,
        admin_group=settings.AUTHENTIK_ADMIN_GROUP,
        expert_group=settings.AUTHENTIK_EXPERT_GROUP,
    )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun pengguna tidak aktif.",
        )
    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """FastAPI dependency yang memastikan user memiliki role admin.

    Args:
        current_user: User yang sedang login (dari dependency get_current_user).

    Returns:
        Instance User dengan role admin.

    Raises:
        HTTPException: Jika user tidak memiliki role admin (403).
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak. Diperlukan role admin.",
        )
    return current_user


async def require_expert(current_user: User = Depends(get_current_user)) -> User:
    """FastAPI dependency yang memastikan user memiliki role expert atau admin.

    Args:
        current_user: User yang sedang login (dari dependency get_current_user).

    Returns:
        Instance User dengan role expert atau admin.

    Raises:
        HTTPException: Jika user tidak memiliki role yang sesuai (403).
    """
    if current_user.role not in ("admin", "expert"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak.",
        )
    return current_user
