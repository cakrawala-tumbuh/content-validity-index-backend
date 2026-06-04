"""Migrasi: tambahkan kolom full_name_overridden ke tabel users.

Menambahkan flag boolean untuk menandai bahwa `full_name` seorang pengguna
telah diedit manual melalui endpoint identitas pribadi (PATCH /users/me),
sehingga nilai tersebut tidak ditimpa lagi oleh sinkronisasi Authentik.

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-04 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Menambahkan kolom full_name_overridden ke tabel users."""
    op.add_column(
        "users",
        sa.Column(
            "full_name_overridden",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment="True jika full_name diedit manual pengguna (tidak ditimpa sync Authentik)",
        ),
    )


def downgrade() -> None:
    """Menghapus kolom full_name_overridden dari tabel users."""
    op.drop_column("users", "full_name_overridden")
