"""Preprocessing configuration and execution ORM models."""

from typing import Optional
from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PreprocessingConfig(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Configuration template for preprocessing (auto or user-defined)."""

    __tablename__ = "preprocessing_configs"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    mode: Mapped[str] = mapped_column(String(50), default="auto", nullable=False)  # auto, user_defined
    configuration: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class PreprocessingRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Execution run of biomedical preprocessing on a dataset version."""

    __tablename__ = "preprocessing_runs"

    dataset_version_id: Mapped[str] = mapped_column(ForeignKey("dataset_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    preprocessing_config_id: Mapped[Optional[str]] = mapped_column(ForeignKey("preprocessing_configs.id", ondelete="SET NULL"), nullable=True)
    
    # pending, planning, awaiting_approval, running, completed, failed
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    approval_status: Mapped[str] = mapped_column(String(50), default="not_required", nullable=False)  # not_required, pending, approved, rejected
    plan: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    report_artifact_id: Mapped[Optional[str]] = mapped_column(ForeignKey("artifacts.id", ondelete="SET NULL"), nullable=True)
    processed_artifact_id: Mapped[Optional[str]] = mapped_column(ForeignKey("artifacts.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    dataset_version = relationship("DatasetVersion", back_populates="preprocessing_runs")
