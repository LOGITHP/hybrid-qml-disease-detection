"""Training configuration and execution run ORM models."""

from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TrainingConfig(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Generic training hyperparameters entity."""

    __tablename__ = "training_configs"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    epochs: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    batch_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    learning_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    optimizer: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    random_seed: Mapped[int] = mapped_column(Integer, default=42, nullable=False)
    early_stopping: Mapped[bool] = mapped_column(Integer, default=True, nullable=False)
    extra_config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class TrainingRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """End-to-end model training execution record tying dataset, preprocessing, features, and model."""

    __tablename__ = "training_runs"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    model_id: Mapped[str] = mapped_column(ForeignKey("models.id", ondelete="CASCADE"), nullable=False, index=True)
    model_version_id: Mapped[Optional[str]] = mapped_column(ForeignKey("model_versions.id", ondelete="SET NULL"), nullable=True)
    dataset_version_id: Mapped[str] = mapped_column(ForeignKey("dataset_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    preprocessing_run_id: Mapped[Optional[str]] = mapped_column(ForeignKey("preprocessing_runs.id", ondelete="SET NULL"), nullable=True)
    feature_selection_run_id: Mapped[str] = mapped_column(ForeignKey("feature_selection_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    training_config_id: Mapped[Optional[str]] = mapped_column(ForeignKey("training_configs.id", ondelete="SET NULL"), nullable=True)

    # queued, preparing, running, evaluating, saving, completed, failed, cancelled
    status: Mapped[str] = mapped_column(String(50), default="queued", nullable=False)
    metrics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    artifact_id: Mapped[Optional[str]] = mapped_column(ForeignKey("artifacts.id", ondelete="SET NULL"), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    model_version = relationship("ModelVersion", back_populates="training_runs")
    feature_selection_run = relationship("FeatureSelectionRun", back_populates="training_runs")
