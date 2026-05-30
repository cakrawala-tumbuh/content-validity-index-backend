"""Service untuk pengelolaan Dimension."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dimension import Dimension
from app.repositories.dimension_repository import DimensionRepository
from app.schemas.dimension import DimensionBulkCreate, DimensionCreate, DimensionUpdate


class DimensionService:
    """Service yang menangani business logic untuk entitas Dimension.

    Args:
        db: AsyncSession database yang aktif.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Inisialisasi DimensionService.

        Args:
            db: AsyncSession database yang aktif.
        """
        self.db = db
        self.repo = DimensionRepository(db)

    async def get_by_instrument(self, instrument_id: str) -> list[Dimension]:
        """Mengambil semua dimensi dalam sebuah instrumen.

        Args:
            instrument_id: ID instrumen.

        Returns:
            Daftar Dimension diurutkan berdasarkan nama.
        """
        return await self.repo.get_by_instrument(instrument_id)

    async def get_by_id(self, dimension_id: str, instrument_id: str) -> Dimension:
        """Mengambil dimensi berdasarkan ID dan memvalidasi kepemilikannya.

        Args:
            dimension_id: ID unik dimensi.
            instrument_id: ID instrumen pemilik dimensi.

        Returns:
            Instance Dimension.

        Raises:
            HTTPException: Jika dimensi tidak ditemukan atau bukan milik instrumen (404).
        """
        dimension = await self.repo.get_by_id(dimension_id)
        if not dimension or dimension.instrument_id != instrument_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dimensi dengan ID '{dimension_id}' tidak ditemukan.",
            )
        return dimension

    async def create(self, instrument_id: str, data: DimensionCreate) -> Dimension:
        """Membuat dimensi baru dalam sebuah instrumen.

        Args:
            instrument_id: ID instrumen tempat dimensi dibuat.
            data: Data dimensi baru.

        Returns:
            Instance Dimension yang sudah dibuat.
        """
        dimension = Dimension(
            id=str(uuid.uuid4()),
            instrument_id=instrument_id,
            name=data.name,
            description=data.description,
        )
        return await self.repo.create(dimension)

    async def bulk_create(
        self, instrument_id: str, data: DimensionBulkCreate
    ) -> list[Dimension]:
        """Membuat banyak dimensi sekaligus dalam sebuah instrumen.

        Args:
            instrument_id: ID instrumen tempat dimensi dibuat.
            data: Data berisi daftar dimensi yang akan dibuat.

        Returns:
            Daftar Instance Dimension yang sudah dibuat.
        """
        dimensions = [
            Dimension(
                id=str(uuid.uuid4()),
                instrument_id=instrument_id,
                name=dim_data.name,
                description=dim_data.description,
            )
            for dim_data in data.dimensions
        ]
        return await self.repo.bulk_create(dimensions)

    async def update(
        self, dimension_id: str, instrument_id: str, data: DimensionUpdate
    ) -> Dimension:
        """Memperbarui data dimensi.

        Args:
            dimension_id: ID dimensi yang akan diperbarui.
            instrument_id: ID instrumen pemilik dimensi.
            data: Data pembaruan dimensi.

        Returns:
            Instance Dimension yang sudah diperbarui.

        Raises:
            HTTPException: Jika dimensi tidak ditemukan (404).
        """
        dimension = await self.get_by_id(dimension_id, instrument_id)
        if data.name is not None:
            dimension.name = data.name
        if data.description is not None:
            dimension.description = data.description
        return await self.repo.update(dimension)

    async def delete(self, dimension_id: str, instrument_id: str) -> None:
        """Menghapus dimensi dari instrumen.

        Args:
            dimension_id: ID dimensi yang akan dihapus.
            instrument_id: ID instrumen pemilik dimensi.

        Raises:
            HTTPException: Jika dimensi tidak ditemukan (404).
        """
        dimension = await self.get_by_id(dimension_id, instrument_id)
        await self.repo.delete(dimension)