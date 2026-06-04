"""Model SQLAlchemy untuk entitas User."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.expertise_area import ExpertiseArea, user_expertise_areas


class User(Base):
    """Model SQLAlchemy untuk tabel users.

    Menyimpan data pengguna yang disinkronisasi dari JWT Authentik.
    Role pengguna (admin/expert) dipetakan dari Authentik groups claim.
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="ID unik pengguna (sub dari JWT Authentik)",
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name_overridden: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="True jika full_name diedit manual pengguna (tidak ditimpa sync Authentik)",
    )
    institution: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="expert",
        comment="Role pengguna: admin atau expert",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Bidang keahlian (many-to-many). Dimuat eager (selectin) agar aman diakses
    # dalam konteks async tanpa lazy-load tambahan.
    expertise_areas: Mapped[list[ExpertiseArea]] = relationship(
        secondary=user_expertise_areas,
        lazy="selectin",
        order_by=ExpertiseArea.name,
    )
