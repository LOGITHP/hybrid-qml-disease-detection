"""Model, ModelConfig, and ModelVersion ORM database models."""

from typing import List, Optional
from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Model(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Model registry root entity."""

    __tablename__ = "models"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    model_type: Mapped[str] = mapped_column(String(50), nullable=False)  # svm_linear, svm_rbf, vqc
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="models")
    configs = relationship("ModelConfig", back_populates="model", cascade="all, delete-orphan")
    versions = relationship("ModelVersion", back_populates="model", cascade="all, delete-orphan")


class ModelConfig(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Model architecture and hyperparameter configuration template."""

    __tablename__ = "model_configs"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    model_id: Mapped[str] = mapped_column(ForeignKey("models.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hyperparameters: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    model = relationship("Model", back_populates="configs")


class ModelVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Specific trained version of a model with associated weights/pipeline artifact."""

    __tablename__ = "model_versions"

    model_id: Mapped[str] = mapped_column(ForeignKey("models.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    version_tag: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "v1.0.0"
    artifact_id: Mapped[Optional[str]] = mapped_column(ForeignKey("artifacts.id", ondelete="SET NULL"), nullable=True)
    metrics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # validation metrics
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)  # active, archived, deprecated

    # Relationships
    model = relationship("Model", back_populates="versions")
    training_runs = relationship("TrainingRun", back_populates="model_version")
