"""Migrasi: tambahkan kolom warna latar (background_color) ke tabel domains.

Menambahkan satu kolom hex opsional pada tabel domains untuk menyimpan warna
latar dimensi. Warna ini dipakai sebagai latar baris/sel item milik dimensi
tersebut pada tabel penilaian expert, serta sebagai keterangan (legenda) warna
pada tabel master dimensi.

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-04 01:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Menambahkan kolom background_color ke tabel domains."""
    op.add_column(
        "domains",
        sa.Column("background_color", sa.String(length=7), nullable=True),
    )


def downgrade() -> None:
    """Menghapus kolom background_color dari tabel domains."""
    op.drop_column("domains", "background_color")
