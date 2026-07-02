"""Migrasi: tambahkan kolom is_active ke tabel expert_assignments.

Menambahkan kolom boolean is_active untuk mendukung penonaktifan penilaian expert.
Ketika sebuah penilaian dinonaktifkan admin, assignment tidak dihapus melainkan
ditandai is_active=False sehingga tidak diperhitungkan dalam kalkulasi CVI.
Semua baris lama diberi nilai default True (tetap diperhitungkan).

Revision ID: 0009
Revises: 0008
Create Date: 2026-07-02 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Menambahkan kolom is_active dengan default True."""
    op.add_column(
        "expert_assignments",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment=(
                "True jika penilaian diperhitungkan dalam kalkulasi CVI; "
                "False jika dinonaktifkan admin (data tetap disimpan, tidak dihitung)."
            ),
        ),
    )


def downgrade() -> None:
    """Menghapus kolom is_active."""
    op.drop_column("expert_assignments", "is_active")
