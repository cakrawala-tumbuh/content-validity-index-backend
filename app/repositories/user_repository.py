"""Repository untuk operasi database entitas User."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Repository untuk operasi CRUD pada tabel users.

    Args:
        db: AsyncSession database yang aktif.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Inisialisasi UserRepository.

        Args:
            db: AsyncSession database yang aktif.
        """
        self.db = db

    async def get_by_id(self, user_id: str) -> User | None:
        """Mengambil user berdasarkan ID.

        Args:
            user_id: ID unik user.

        Returns:
            Instance User jika ditemukan, None jika tidak.
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Mengambil user berdasarkan email.

        Args:
            email: Alamat email user.

        Returns:
            Instance User jika ditemukan, None jika tidak.
        """
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Mengambil semua user dengan pagination.

        Args:
            skip: Jumlah record yang dilewati.
            limit: Jumlah maksimal record yang dikembalikan.

        Returns:
            Daftar User.
        """
        result = await self.db.execute(select(User).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create(self, user: User) -> User:
        """Menyimpan user baru ke database.

        Args:
            user: Instance User yang akan disimpan.

        Returns:
            Instance User yang sudah disimpan.
        """
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update(self, user: User) -> User:
        """Memperbarui data user di database.

        Args:
            user: Instance User dengan data yang sudah diubah.

        Returns:
            Instance User yang sudah diperbarui.
        """
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        """Menghapus user dari database.

        Args:
            user: Instance User yang akan dihapus.
        """
        await self.db.delete(user)
        await self.db.flush()
