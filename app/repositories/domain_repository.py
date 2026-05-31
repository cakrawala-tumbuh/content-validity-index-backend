"""Repository untuk operasi database entitas Domain."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Domain


class DomainRepository:
    """Repository untuk operasi CRUD pada tabel domains.

    Args:
        db: AsyncSession database yang aktif.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Inisialisasi DomainRepository.

        Args:
            db: AsyncSession database yang aktif.
        """
        self.db = db

    async def get_by_id(self, domain_id: str) -> Domain | None:
        """Mengambil domain berdasarkan ID.

        Args:
            domain_id: ID unik domain.

        Returns:
            Instance Domain jika ditemukan, None jika tidak.
        """
        result = await self.db.execute(select(Domain).where(Domain.id == domain_id))
        return result.scalar_one_or_none()

    async def get_by_instrument(self, instrument_id: str) -> list[Domain]:
        """Mengambil semua domain dalam sebuah instrumen.

        Args:
            instrument_id: ID instrumen.

        Returns:
            Daftar Domain dalam instrumen tersebut.
        """
        result = await self.db.execute(
            select(Domain).where(Domain.instrument_id == instrument_id).order_by(Domain.name)
        )
        return list(result.scalars().all())

    async def create(self, domain: Domain) -> Domain:
        """Menyimpan domain baru ke database.

        Args:
            domain: Instance Domain yang akan disimpan.

        Returns:
            Instance Domain yang sudah disimpan.
        """
        self.db.add(domain)
        await self.db.flush()
        await self.db.refresh(domain)
        return domain

    async def update(self, domain: Domain) -> Domain:
        """Memperbarui data domain di database.

        Args:
            domain: Instance Domain dengan data yang sudah diubah.

        Returns:
            Instance Domain yang sudah diperbarui.
        """
        await self.db.flush()
        await self.db.refresh(domain)
        return domain

    async def delete(self, domain: Domain) -> None:
        """Menghapus domain dari database.

        Args:
            domain: Instance Domain yang akan dihapus.
        """
        await self.db.delete(domain)
        await self.db.flush()
