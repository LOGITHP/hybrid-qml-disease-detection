"""Experiment entity ORM model for grouping multi-run studies and comparisons."""

from typing import Optional
from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Experiment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """High-level experiment container tracking pipelines and model benchmarks."""

    __tablename__ = "experiments"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)

    # Relationships
    user = relationship("User", back_populates="experiments")
