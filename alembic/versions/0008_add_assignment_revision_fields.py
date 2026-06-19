"""Migrasi: tambahkan kolom revisi ke tabel expert_assignments.

Menambahkan dua kolom pada tabel expert_assignments untuk mendukung mekanisme
pengarsipan evaluasi. Ketika ditemukan kesalahan pada hasil penilaian, assignment
lama tidak dihapus melainkan diarsipkan (status='archived'); assignment baru
dibuat dengan salinan isian sebelumnya agar expert dapat merevisi.

- previous_assignment_id: FK ke assignment asal (dapat NULL jika ini bukan revisi).
- revision_number: Nomor revisi, dimulai dari 1 dan bertambah setiap revisi.

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-19 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Menambahkan kolom previous_assignment_id dan revision_number."""
    op.add_column(
        "expert_assignments",
        sa.Column(
            "previous_assignment_id",
            sa.String(36),
            sa.ForeignKey("expert_assignments.id", ondelete="SET NULL"),
            nullable=True,
            comment="ID assignment sebelumnya yang diarsipkan (untuk tracking riwayat revisi).",
        ),
    )
    op.add_column(
        "expert_assignments",
        sa.Column(
            "revision_number",
            sa.Integer,
            nullable=False,
            server_default="1",
            comment="Nomor revisi. Dimulai dari 1; bertambah setiap kali assignment diarsipkan.",
        ),
    )
    op.create_index(
        "ix_expert_assignments_previous_assignment_id",
        "expert_assignments",
        ["previous_assignment_id"],
    )


def downgrade() -> None:
    """Menghapus kolom previous_assignment_id dan revision_number."""
    op.drop_index(
        "ix_expert_assignments_previous_assignment_id",
        table_name="expert_assignments",
    )
    op.drop_column("expert_assignments", "previous_assignment_id")
    op.drop_column("expert_assignments", "revision_number")
