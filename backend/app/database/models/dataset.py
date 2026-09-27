"""Dataset and DatasetVersion ORM models."""

from typing import List, Optional
from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Dataset(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Dataset entity representing a biomedical study or disease data source."""

    __tablename__ = "datasets"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="datasets")
    versions = relationship("DatasetVersion", back_populates="dataset", cascade="all, delete-orphan")


class DatasetVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Specific version of an uploaded dataset."""

    __tablename__ = "dataset_versions"

    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    version_tag: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "v1.0"
    file_artifact_id: Mapped[Optional[str]] = mapped_column(ForeignKey("artifacts.id", ondelete="SET NULL"), nullable=True)
    row_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    column_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="uploaded", nullable=False)  # uploaded, validated, failed
    dataset_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    dataset = relationship("Dataset", back_populates="versions")
    preprocessing_runs = relationship("PreprocessingRun", back_populates="dataset_version", cascade="all, delete-orphan")
    feature_selection_runs = relationship("FeatureSelectionRun", back_populates="dataset_version", cascade="all, delete-orphan")
