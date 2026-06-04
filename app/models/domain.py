"""Model SQLAlchemy untuk entitas Domain (dimensi pengelompokan item)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Domain(Base):
    """Model SQLAlchemy untuk tabel domains.

    Domain merepresentasikan dimensi/kelompok tematik dalam sebuah instrumen CVI.
    Setiap instrumen dapat memiliki beberapa domain, dan setiap item dapat
    dikelompokkan ke dalam satu domain.

    Contoh domain: "Literasi Kesehatan", "Akses Informasi", "Komunikasi".
    """

    __tablename__ = "domains"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    instrument_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("instruments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Nama domain/dimensi",
    )
    construct_definition: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Definisi konstruk dari kisi-kisi (kolom D)",
    )
    behavioral_indicator_example: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Contoh indikator perilaku dari kisi-kisi (kolom E)",
    )
    theory_reference: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Referensi teori dari kisi-kisi (kolom F)",
    )
    background_color: Mapped[str | None] = mapped_column(
        String(7),
        nullable=True,
        comment="Warna latar dimensi dalam format hex #RRGGBB untuk tabel penilaian",
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
