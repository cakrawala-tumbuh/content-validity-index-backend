"""Migrasi: tambahkan tabel dimensions dan ubah kolom domain pada items.

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-31 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Membuat tabel dimensions dan memigrasi kolom domain item menjadi dimension_id."""
    # 1. Buat tabel dimensions
    op.create_table(
        "dimensions",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("instrument_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["instrument_id"], ["instruments.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dimensions_instrument_id", "dimensions", ["instrument_id"])

    # 2. Tambah kolom dimension_id ke items
    op.add_column(
        "items",
        sa.Column("dimension_id", sa.String(36), nullable=True),
    )
    op.create_foreign_key(
        "fk_items_dimension_id",
        "items",
        "dimensions",
        ["dimension_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_items_dimension_id", "items", ["dimension_id"])

    # 3. Hapus kolom domain yang lama
    op.drop_column("items", "domain")


def downgrade() -> None:
    """Mengembalikan ke skema sebelumnya."""
    # Kembalikan kolom domain
    op.add_column(
        "items",
        sa.Column("domain", sa.String(255), nullable=True),
    )

    # Hapus constraint dan kolom dimension_id
    op.drop_constraint("fk_items_dimension_id", "items", type_="foreignkey")
    op.drop_index("ix_items_dimension_id", table_name="items")
    op.drop_column("items", "dimension_id")

    # Hapus tabel dimensions
    op.drop_table("dimensions")