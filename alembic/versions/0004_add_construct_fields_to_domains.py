"""Migrasi: tambahkan kolom kisi-kisi konstruk (D/E/F) ke tabel domains.

Menambahkan tiga kolom teks opsional pada tabel domains untuk menyimpan
isi kisi-kisi konstruk dari instrumen:
- construct_definition (kolom D: Definisi Konstruk)
- behavioral_indicator_example (kolom E: Contoh Indikator Perilaku)
- theory_reference (kolom F: Referensi Teori)

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-02 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Menambahkan kolom kisi-kisi konstruk ke tabel domains."""
    op.add_column(
        "domains",
        sa.Column("construct_definition", sa.Text(), nullable=True),
    )
    op.add_column(
        "domains",
        sa.Column("behavioral_indicator_example", sa.Text(), nullable=True),
    )
    op.add_column(
        "domains",
        sa.Column("theory_reference", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Menghapus kolom kisi-kisi konstruk dari tabel domains."""
    op.drop_column("domains", "theory_reference")
    op.drop_column("domains", "behavioral_indicator_example")
    op.drop_column("domains", "construct_definition")
