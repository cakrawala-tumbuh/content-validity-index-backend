"""Service untuk pengelolaan ExpertiseArea (bidang keahlian)."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expertise_area import ExpertiseArea
from app.repositories.expertise_area_repository import ExpertiseAreaRepository
from app.schemas.expertise_area import ExpertiseAreaCreate, ExpertiseAreaUpdate


class ExpertiseAreaService:
    """Service yang menangani business logic untuk entitas ExpertiseArea.

    Args:
        db: AsyncSession database yang aktif.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Inisialisasi ExpertiseAreaService.

        Args:
            db: AsyncSession database yang aktif.
        """
        self.db = db
        self.repo = ExpertiseAreaRepository(db)

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[ExpertiseArea]:
        """Mengambil semua bidang keahlian.

        Args:
            skip: Jumlah record yang dilewati.
            limit: Jumlah maksimal record yang dikembalikan.

        Returns:
            Daftar ExpertiseArea.
        """
        return await self.repo.get_all(skip=skip, limit=limit)

    async def get_by_id(self, expertise_area_id: str) -> ExpertiseArea:
        """Mengambil bidang keahlian berdasarkan ID.

        Args:
            expertise_area_id: ID unik bidang keahlian.

        Returns:
            Instance ExpertiseArea.

        Raises:
            HTTPException: Jika bidang keahlian tidak ditemukan (404).
        """
        area = await self.repo.get_by_id(expertise_area_id)
        if not area:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bidang keahlian dengan ID '{expertise_area_id}' tidak ditemukan.",
            )
        return area

    async def create(self, data: ExpertiseAreaCreate) -> ExpertiseArea:
        """Membuat bidang keahlian baru (admin only).

        Args:
            data: Data bidang keahlian baru.

        Returns:
            Instance ExpertiseArea yang sudah dibuat.

        Raises:
            HTTPException: Jika nama bidang keahlian sudah dipakai (409).
        """
        existing = await self.repo.get_by_name(data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Bidang keahlian dengan nama '{data.name}' sudah ada.",
            )
        area = ExpertiseArea(
            id=str(uuid.uuid4()),
            name=data.name,
            description=data.description,
        )
        return await self.repo.create(area)

    async def update(self, expertise_area_id: str, data: ExpertiseAreaUpdate) -> ExpertiseArea:
        """Memperbarui data bidang keahlian (admin only).

        Args:
            expertise_area_id: ID bidang keahlian yang akan diperbarui.
            data: Data pembaruan bidang keahlian.

        Returns:
            Instance ExpertiseArea yang sudah diperbarui.

        Raises:
            HTTPException: Jika bidang keahlian tidak ditemukan (404) atau nama
                baru sudah dipakai bidang keahlian lain (409).
        """
        area = await self.get_by_id(expertise_area_id)
        if data.name is not None and data.name != area.name:
            existing = await self.repo.get_by_name(data.name)
            if existing and existing.id != area.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Bidang keahlian dengan nama '{data.name}' sudah ada.",
                )
            area.name = data.name
        if "description" in data.model_fields_set:
            area.description = data.description
        return await self.repo.update(area)

    async def delete(self, expertise_area_id: str) -> None:
        """Menghapus bidang keahlian (admin only).

        Penghapusan juga melepaskan keterkaitannya dengan pengguna mana pun
        melalui cascade pada tabel asosiasi.

        Args:
            expertise_area_id: ID bidang keahlian yang akan dihapus.

        Raises:
            HTTPException: Jika bidang keahlian tidak ditemukan (404).
        """
        area = await self.get_by_id(expertise_area_id)
        await self.repo.delete(area)
