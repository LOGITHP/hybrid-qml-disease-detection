"""Artifact metadata tracking ORM model."""

from typing import Optional
from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Artifact(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Metadata record for stored files (datasets, pipelines, reports, models)."""

    __tablename__ = "artifacts"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # dataset_csv, fitted_pipeline, model_binary, report_json, metrics_json, etc.
    artifact_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    mime_type: Mapped[str] = mapped_column(String(100), default="application/octet-stream", nullable=False)
    checksum: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # SHA-256

    # Relationships
    user = relationship("User", back_populates="artifacts")
