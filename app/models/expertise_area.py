"""Model SQLAlchemy untuk entitas ExpertiseArea (bidang keahlian).

Bidang keahlian merupakan daftar master yang dikelola oleh admin. Seorang
expert dapat memiliki lebih dari satu bidang keahlian melalui relasi
many-to-many lewat tabel asosiasi `user_expertise_areas`.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Table, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

#: Tabel asosiasi many-to-many antara users dan expertise_areas.
user_expertise_areas = Table(
    "user_expertise_areas",
    Base.metadata,
    Column(
        "user_id",
        String(255),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "expertise_area_id",
        String(36),
        ForeignKey("expertise_areas.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class ExpertiseArea(Base):
    """Model SQLAlchemy untuk tabel expertise_areas.

    Merepresentasikan satu bidang keahlian dalam daftar master. Entri pada
    tabel ini hanya dapat dibuat/diubah/dihapus oleh admin, namun dapat
    dibaca oleh semua pengguna untuk dipilih sebagai keahlian mereka.

    Contoh: "Psikologi Pendidikan", "Pengukuran", "Statistika".
    """

    __tablename__ = "expertise_areas"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        comment="Nama bidang keahlian (unik)",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Deskripsi singkat bidang keahlian (opsional)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
