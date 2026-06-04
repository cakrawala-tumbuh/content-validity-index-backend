"""Migrasi: tambahkan master bidang keahlian dan relasi many-to-many ke user.

Membuat tabel master `expertise_areas` dan tabel asosiasi
`user_expertise_areas`, lalu menghapus kolom teks bebas lama
`users.expertise_area` (data lama tidak dimigrasikan).

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-04 00:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Membuat tabel bidang keahlian + asosiasi, dan menghapus kolom lama."""
    op.create_table(
        "expertise_areas",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_expertise_areas_name", "expertise_areas", ["name"], unique=True)

    op.create_table(
        "user_expertise_areas",
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("expertise_area_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["expertise_area_id"], ["expertise_areas.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "expertise_area_id"),
    )

    op.drop_column("users", "expertise_area")


def downgrade() -> None:
    """Mengembalikan kolom lama dan menghapus tabel bidang keahlian + asosiasi."""
    op.add_column(
        "users",
        sa.Column("expertise_area", sa.String(length=500), nullable=True),
    )
    op.drop_table("user_expertise_areas")
    op.drop_index("ix_expertise_areas_name", table_name="expertise_areas")
    op.drop_table("expertise_areas")
