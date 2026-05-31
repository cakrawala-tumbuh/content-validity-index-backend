"""Migrasi: tambahkan tabel domains dan ubah kolom domain ke domain_id di items.

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-31 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Membuat tabel domains dan mengubah kolom domain ke domain_id di items."""
    # Buat tabel domains
    op.create_table(
        "domains",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("instrument_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_domains_instrument_id", "domains", ["instrument_id"])

    # Hapus kolom domain dari items
    op.drop_column("items", "domain")

    # Tambah kolom domain_id dengan FK ke domains
    op.add_column(
        "items",
        sa.Column("domain_id", sa.String(36), nullable=True),
    )
    op.create_foreign_key(
        "fk_items_domain_id_domains",
        "items",
        "domains",
        ["domain_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_items_domain_id", "items", ["domain_id"])


def downgrade() -> None:
    """Mengembalikan ke skema semula."""
    # Hapus FK dan kolom domain_id
    op.drop_index("ix_items_domain_id", table_name="items")
    op.drop_constraint("fk_items_domain_id_domains", "items", type_="foreignkey")
    op.drop_column("items", "domain_id")

    # Kembalikan kolom domain
    op.add_column(
        "items",
        sa.Column("domain", sa.String(255), nullable=True),
    )

    # Hapus tabel domains
    op.drop_index("ix_domains_instrument_id", table_name="domains")
    op.drop_table("domains")
