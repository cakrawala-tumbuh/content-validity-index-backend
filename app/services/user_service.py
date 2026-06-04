"""Service untuk pengelolaan data User."""

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expertise_area import ExpertiseArea
from app.models.user import User
from app.repositories.expertise_area_repository import ExpertiseAreaRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserSelfUpdate, UserUpdate


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
        self.expertise_repo = ExpertiseAreaRepository(db)

    async def _resolve_expertise_areas(self, ids: list[str]) -> list[ExpertiseArea]:
        """Mengambil objek ExpertiseArea dari daftar ID dan memvalidasinya.

        Args:
            ids: Daftar ID bidang keahlian yang diminta.

        Returns:
            Daftar instance ExpertiseArea yang sesuai. List kosong jika `ids` kosong.

        Raises:
            HTTPException: Jika ada ID yang tidak ditemukan (400).
        """
        if not ids:
            return []
        unique_ids = list(dict.fromkeys(ids))
        areas = await self.expertise_repo.get_by_ids(unique_ids)
        found_ids = {area.id for area in areas}
        missing = [area_id for area_id in unique_ids if area_id not in found_ids]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bidang keahlian tidak ditemukan: {', '.join(missing)}.",
            )
        return areas

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
            # Jangan timpa nama yang sudah diedit manual oleh pengguna.
            if not existing.full_name_overridden:
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
        if data.expertise_area_ids is not None:
            user.expertise_areas = await self._resolve_expertise_areas(data.expertise_area_ids)
        if data.is_active is not None:
            user.is_active = data.is_active
        return await self.repo.update(user)

    async def update_self(self, user_id: str, data: UserSelfUpdate) -> User:
        """Memperbarui identitas pribadi milik pengguna sendiri.

        Mengizinkan pengguna mengubah `full_name`, `institution`, dan daftar
        bidang keahlian. Saat `full_name` diubah, flag `full_name_overridden`
        diset True agar tidak ditimpa lagi oleh sinkronisasi Authentik.

        Args:
            user_id: ID unik pengguna yang sedang login.
            data: Data pembaruan identitas pribadi.

        Returns:
            Instance User yang sudah diperbarui.

        Raises:
            HTTPException: Jika user tidak ditemukan (404) atau nama lengkap
                kosong setelah di-trim (400).
        """
        user = await self.get_by_id(user_id)
        if data.full_name is not None:
            full_name = data.full_name.strip()
            if not full_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Nama lengkap tidak boleh kosong.",
                )
            user.full_name = full_name
            user.full_name_overridden = True
        if data.institution is not None:
            user.institution = data.institution
        if data.expertise_area_ids is not None:
            user.expertise_areas = await self._resolve_expertise_areas(data.expertise_area_ids)
        return await self.repo.update(user)
