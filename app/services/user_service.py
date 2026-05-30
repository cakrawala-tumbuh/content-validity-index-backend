"""Service untuk pengelolaan data User."""

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserUpdate


class UserService:
    """Service yang menangani business logic untuk entitas User.

    Args:
        db: AsyncSession database yang aktif.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Inisialisasi UserService.

        Args:
            db: AsyncSession database yang aktif.
        """
        self.db = db
        self.repo = UserRepository(db)

    async def sync_from_claims(
        self, claims: dict[str, Any], admin_group: str, expert_group: str
    ) -> User:
        """Sinkronisasi user ke database lokal dari JWT claims Authentik.

        Jika user sudah ada, data diperbarui. Jika belum ada, user baru dibuat.
        Role ditentukan dari keanggotaan grup Authentik.

        Args:
            claims: Dict berisi JWT claims dari Authentik.
            admin_group: Nama grup Authentik untuk role admin.
            expert_group: Nama grup Authentik untuk role expert.

        Returns:
            Instance User yang sudah disinkronisasi.
        """
        user_id: str = claims["sub"]
        email: str = claims.get("email", "")
        full_name: str = claims.get("name", claims.get("preferred_username", email))
        groups: list[str] = claims.get("groups", [])

        if admin_group in groups:
            role = "admin"
        elif expert_group in groups:
            role = "expert"
        else:
            role = "expert"

        existing = await self.repo.get_by_id(user_id)
        if existing:
            existing.email = email
            existing.full_name = full_name
            existing.role = role
            return await self.repo.update(existing)

        new_user = User(
            id=user_id,
            email=email,
            full_name=full_name,
            role=role,
        )
        return await self.repo.create(new_user)

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Mengambil semua user (admin only).

        Args:
            skip: Jumlah record yang dilewati.
            limit: Jumlah maksimal record yang dikembalikan.

        Returns:
            Daftar User.
        """
        return await self.repo.get_all(skip=skip, limit=limit)

    async def get_by_id(self, user_id: str) -> User:
        """Mengambil user berdasarkan ID.

        Args:
            user_id: ID unik user.

        Returns:
            Instance User.

        Raises:
            HTTPException: Jika user tidak ditemukan (404).
        """
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User dengan ID '{user_id}' tidak ditemukan.",
            )
        return user

    async def update(self, user_id: str, data: UserUpdate) -> User:
        """Memperbarui profil user.

        Args:
            user_id: ID unik user yang akan diperbarui.
            data: Data pembaruan user.

        Returns:
            Instance User yang sudah diperbarui.

        Raises:
            HTTPException: Jika user tidak ditemukan (404).
        """
        user = await self.get_by_id(user_id)
        if data.institution is not None:
            user.institution = data.institution
        if data.expertise_area is not None:
            user.expertise_area = data.expertise_area
        if data.is_active is not None:
            user.is_active = data.is_active
        return await self.repo.update(user)
