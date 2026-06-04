"""Service untuk pengelolaan Domain."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Domain
from app.repositories.domain_repository import DomainRepository
from app.schemas.domain import DomainCreate, DomainUpdate


class DomainService:
    """Service yang menangani business logic untuk entitas Domain.

    Args:
        db: AsyncSession database yang aktif.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Inisialisasi DomainService.

        Args:
            db: AsyncSession database yang aktif.
        """
        self.db = db
        self.repo = DomainRepository(db)

    async def get_by_instrument(self, instrument_id: str) -> list[Domain]:
        """Mengambil semua domain dalam sebuah instrumen.

        Args:
            instrument_id: ID instrumen.

        Returns:
            Daftar Domain dalam instrumen.
        """
        return await self.repo.get_by_instrument(instrument_id)

    async def get_by_id(self, domain_id: str, instrument_id: str) -> Domain:
        """Mengambil domain berdasarkan ID dan memvalidasi kepemilikannya.

        Args:
            domain_id: ID unik domain.
            instrument_id: ID instrumen pemilik domain.

        Returns:
            Instance Domain.

        Raises:
            HTTPException: Jika domain tidak ditemukan atau tidak milik instrumen tersebut (404).
        """
        domain = await self.repo.get_by_id(domain_id)
        if not domain or domain.instrument_id != instrument_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Domain dengan ID '{domain_id}' tidak ditemukan.",
            )
        return domain

    async def create(self, instrument_id: str, data: DomainCreate) -> Domain:
        """Membuat domain baru dalam sebuah instrumen.

        Args:
            instrument_id: ID instrumen tempat domain dibuat.
            data: Data domain baru.

        Returns:
            Instance Domain yang sudah dibuat.
        """
        domain = Domain(
            id=str(uuid.uuid4()),
            instrument_id=instrument_id,
            name=data.name,
            construct_definition=data.construct_definition,
            behavioral_indicator_example=data.behavioral_indicator_example,
            theory_reference=data.theory_reference,
            background_color=data.background_color,
        )
        return await self.repo.create(domain)

    async def update(self, domain_id: str, instrument_id: str, data: DomainUpdate) -> Domain:
        """Memperbarui data domain.

        Args:
            domain_id: ID domain yang akan diperbarui.
            instrument_id: ID instrumen pemilik domain.
            data: Data pembaruan domain.

        Returns:
            Instance Domain yang sudah diperbarui.

        Raises:
            HTTPException: Jika domain tidak ditemukan (404).
        """
        domain = await self.get_by_id(domain_id, instrument_id)
        fields_set = data.model_fields_set
        if data.name is not None:
            domain.name = data.name
        # Field kisi-kisi (D/E/F) boleh di-set null secara eksplisit untuk mengosongkan,
        # sehingga hanya diperbarui jika benar-benar disertakan dalam request.
        if "construct_definition" in fields_set:
            domain.construct_definition = data.construct_definition
        if "behavioral_indicator_example" in fields_set:
            domain.behavioral_indicator_example = data.behavioral_indicator_example
        if "theory_reference" in fields_set:
            domain.theory_reference = data.theory_reference
        if "background_color" in fields_set:
            domain.background_color = data.background_color
        return await self.repo.update(domain)

    async def delete(self, domain_id: str, instrument_id: str) -> None:
        """Menghapus domain dari instrumen.

        Args:
            domain_id: ID domain yang akan dihapus.
            instrument_id: ID instrumen pemilik domain.

        Raises:
            HTTPException: Jika domain tidak ditemukan (404).
        """
        domain = await self.get_by_id(domain_id, instrument_id)
        await self.repo.delete(domain)
