"""Model SQLAlchemy untuk entitas Dimension (dimensi instrumen)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Dimension(Base):
    """Model SQLAlchemy untuk tabel dimensions.

    Dimensi digunakan untuk mengelompokkan item dalam sebuah instrumen.
    Setiap instrumen dapat memiliki banyak dimensi (misalnya: "Stability of Change",
    "Technology Maturity", "Role Clarity", dll.).
    """

    __tablename__ = "dimensions"

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
        comment="Nama dimensi (contoh: Stability of Change, Role Clarity)",
    )
    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Deskripsi opsional dari dimensi",
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

    # Relationships
    instrument: Mapped["Instrument"] = relationship(  # noqa: F821
        "Instrument",
        back_populates="dimensions",
    )