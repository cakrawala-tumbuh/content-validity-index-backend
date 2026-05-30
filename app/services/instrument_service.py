"""Service untuk pengelolaan Instrument."""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.instrument import Instrument
from app.repositories.instrument_repository import InstrumentRepository
from app.schemas.instrument import InstrumentCreate, InstrumentUpdate


class InstrumentService:
    """Service yang menangani business logic untuk entitas Instrument.

    Args:
        db: AsyncSession database yang aktif.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Inisialisasi InstrumentService.

        Args:
            db: AsyncSession database yang aktif.
        """
        self.db = db
        self.repo = InstrumentRepository(db)

    async def get_all(
        self, user_id: str, role: str, skip: int = 0, limit: int = 100
    ) -> list[Instrument]:
        """Mengambil daftar instrumen sesuai role pengguna.

        Admin mendapat semua instrumen; expert hanya yang ditugaskan kepadanya.

        Args:
            user_id: ID pengguna yang meminta.
            role: Role pengguna (admin/expert).
            skip: Jumlah record yang dilewati.
            limit: Jumlah maksimal record yang dikembalikan.

        Returns:
            Daftar Instrument.
        """
        if role == "admin":
            return await self.repo.get_all(skip=skip, limit=limit)
        return await self.repo.get_by_user_assignments(user_id=user_id, skip=skip, limit=limit)

    async def get_by_id(self, instrument_id: str) -> Instrument:
        """Mengambil instrumen berdasarkan ID.

        Args:
            instrument_id: ID unik instrumen.

        Returns:
            Instance Instrument.

        Raises:
            HTTPException: Jika instrumen tidak ditemukan (404).
        """
        instrument = await self.repo.get_by_id(instrument_id)
        if not instrument:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Instrumen dengan ID '{instrument_id}' tidak ditemukan.",
            )
        return instrument

    async def create(self, data: InstrumentCreate, created_by: str) -> Instrument:
        """Membuat instrumen baru.

        Args:
            data: Data instrumen baru.
            created_by: ID admin yang membuat instrumen.

        Returns:
            Instance Instrument yang sudah dibuat.
        """
        instrument = Instrument(
            name=data.name,
            description=data.description,
            version=data.version,
            created_by=created_by,
        )
        return await self.repo.create(instrument)

    async def update(self, instrument_id: str, data: InstrumentUpdate) -> Instrument:
        """Memperbarui data instrumen.

        Args:
            instrument_id: ID instrumen yang akan diperbarui.
            data: Data pembaruan instrumen.

        Returns:
            Instance Instrument yang sudah diperbarui.

        Raises:
            HTTPException: Jika instrumen tidak ditemukan (404).
        """
        instrument = await self.get_by_id(instrument_id)
        if data.name is not None:
            instrument.name = data.name
        if data.description is not None:
            instrument.description = data.description
        if data.version is not None:
            instrument.version = data.version
        if data.status is not None:
            instrument.status = data.status
        return await self.repo.update(instrument)

    async def delete(self, instrument_id: str) -> None:
        """Menghapus instrumen beserta semua data terkait (CASCADE).

        Args:
            instrument_id: ID instrumen yang akan dihapus.

        Raises:
            HTTPException: Jika instrumen tidak ditemukan (404).
        """
        instrument = await self.get_by_id(instrument_id)
        await self.repo.delete(instrument)
