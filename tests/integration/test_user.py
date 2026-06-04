"""Integration test untuk UserRepository dan UserService menggunakan DB in-memory."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expertise_area import ExpertiseArea
from app.models.user import User
from app.repositories.expertise_area_repository import ExpertiseAreaRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserUpdate
from app.services.user_service import UserService


def _make_user(suffix: str = "1") -> User:
    """Membuat instance User untuk keperluan test.

    Args:
        suffix: Suffix untuk membuat ID dan email unik.

    Returns:
        Instance User yang belum disimpan ke DB.
    """
    return User(
        id=f"user-{suffix}",
        email=f"user{suffix}@example.com",
        full_name=f"User {suffix}",
        role="expert",
        is_active=True,
    )


class TestUserRepository:
    """Kumpulan test untuk UserRepository."""

    async def test_create_dan_get_by_id(self, db: AsyncSession) -> None:
        """Harus bisa menyimpan dan mengambil user berdasarkan ID."""
        repo = UserRepository(db)
        user = _make_user("r1")
        created = await repo.create(user)
        assert created.id == "user-r1"
        found = await repo.get_by_id("user-r1")
        assert found is not None
        assert found.email == "userr1@example.com"

    async def test_get_by_email(self, db: AsyncSession) -> None:
        """Harus bisa mengambil user berdasarkan email."""
        repo = UserRepository(db)
        await repo.create(_make_user("r2"))
        found = await repo.get_by_email("userr2@example.com")
        assert found is not None
        assert found.id == "user-r2"

    async def test_get_by_id_tidak_ada(self, db: AsyncSession) -> None:
        """Harus mengembalikan None jika user tidak ada."""
        repo = UserRepository(db)
        found = await repo.get_by_id("nonexistent")
        assert found is None

    async def test_get_all(self, db: AsyncSession) -> None:
        """Harus mengembalikan semua user yang tersimpan."""
        repo = UserRepository(db)
        await repo.create(_make_user("r3"))
        await repo.create(_make_user("r4"))
        users = await repo.get_all()
        ids = [u.id for u in users]
        assert "user-r3" in ids
        assert "user-r4" in ids

    async def test_update(self, db: AsyncSession) -> None:
        """Harus bisa memperbarui field user."""
        repo = UserRepository(db)
        user = _make_user("r5")
        await repo.create(user)
        user.institution = "Universitas Test"
        updated = await repo.update(user)
        assert updated.institution == "Universitas Test"

    async def test_delete(self, db: AsyncSession) -> None:
        """Harus bisa menghapus user dari DB."""
        repo = UserRepository(db)
        user = _make_user("r6")
        await repo.create(user)
        await repo.delete(user)
        assert await repo.get_by_id("user-r6") is None


class TestUserService:
    """Kumpulan test untuk UserService."""

    async def test_sync_from_claims_buat_user_baru(self, db: AsyncSession) -> None:
        """sync_from_claims harus membuat user baru jika belum ada."""
        service = UserService(db)
        claims = {
            "sub": "auth|new-user",
            "email": "newuser@example.com",
            "name": "New User",
            "groups": ["cvi-expert"],
        }
        user = await service.sync_from_claims(claims, "cvi-admin", "cvi-expert")
        assert user.email == "newuser@example.com"
        assert user.role == "expert"

    async def test_sync_from_claims_role_admin(self, db: AsyncSession) -> None:
        """sync_from_claims harus menetapkan role admin jika user ada di group admin."""
        service = UserService(db)
        claims = {
            "sub": "auth|admin-user",
            "email": "admin@example.com",
            "name": "Admin User",
            "groups": ["cvi-admin"],
        }
        user = await service.sync_from_claims(claims, "cvi-admin", "cvi-expert")
        assert user.role == "admin"

    async def test_get_by_id_tidak_ada_raise_404(self, db: AsyncSession) -> None:
        """get_by_id harus raise HTTPException 404 jika user tidak ada."""
        from fastapi import HTTPException

        service = UserService(db)
        with pytest.raises(HTTPException) as exc_info:
            await service.get_by_id("nonexistent-id")
        assert exc_info.value.status_code == 404

    async def test_update_user(self, db: AsyncSession) -> None:
        """update harus memperbarui data user dan mengembalikan user yang diperbarui."""
        service = UserService(db)
        claims = {
            "sub": "auth|update-user",
            "email": "updateuser@example.com",
            "name": "Update User",
            "groups": [],
        }
        user = await service.sync_from_claims(claims, "cvi-admin", "cvi-expert")

        # Siapkan satu bidang keahlian pada daftar master untuk ditautkan.
        area = await ExpertiseAreaRepository(db).create(
            ExpertiseArea(id="area-int-1", name="Kesehatan")
        )

        data = UserUpdate(institution="ITB", expertise_area_ids=[area.id])
        updated = await service.update(user.id, data)
        assert updated.institution == "ITB"
        assert [a.name for a in updated.expertise_areas] == ["Kesehatan"]
