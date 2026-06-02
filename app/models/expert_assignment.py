"""Model SQLAlchemy untuk entitas ExpertAssignment."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func, inspect
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.instrument import Instrument


class ExpertAssignment(Base):
    """Model SQLAlchemy untuk tabel expert_assignments.

    Merepresentasikan penugasan seorang expert ke sebuah instrumen CVI.
    Seorang expert bisa ditugaskan ke lebih dari satu instrumen.

    Status assignment:
        - pending: Expert belum mulai memberikan penilaian.
        - in_progress: Expert sedang dalam proses penilaian.
        - completed: Expert telah menyelesaikan semua penilaian.
    """

    __tablename__ = "expert_assignments"

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
    user_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assigned_by: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
    )
    deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        comment="Status: pending | in_progress | completed",
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    instrument: Mapped[Instrument] = relationship(lazy="selectin")

    @property
    def instrument_name(self) -> str | None:
        """Mengembalikan nama instrumen yang terkait dengan assignment ini.

        Relasi `instrument` dimuat secara eager (lazy="selectin") pada setiap
        query baca, sehingga nama instrumen tersedia tanpa query tambahan.
        Bila relasi belum di-load (misalnya tepat setelah pembuatan assignment),
        method ini mengembalikan None agar tidak memicu lazy-load di konteks async.

        Returns:
            Nama instrumen terkait, atau None jika relasi belum dimuat.
        """
        if "instrument" in inspect(self).unloaded:
            return None
        return self.instrument.name if self.instrument else None
