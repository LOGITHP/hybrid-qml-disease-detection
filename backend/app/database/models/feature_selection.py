"""FeatureSelectionRun ORM model - single source of truth for features consumed by models."""

from typing import List, Optional
from sqlalchemy import ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class FeatureSelectionRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Feature selection execution record.
    
    CRITICAL ARCHITECTURAL PRINCIPLE:
    Feature selection is the single source of truth for feature count and names.
    Both Classical ML (SVM) and Quantum ML (VQC) consume these selected features directly.
    """

    __tablename__ = "feature_selection_runs"

    dataset_version_id: Mapped[str] = mapped_column(ForeignKey("dataset_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    preprocessing_run_id: Mapped[Optional[str]] = mapped_column(ForeignKey("preprocessing_runs.id", ondelete="SET NULL"), nullable=True)

    ranking_method: Mapped[str] = mapped_column(String(100), default="mutual_info", nullable=False)
    feature_count: Mapped[int] = mapped_column(Integer, nullable=False)
    selected_features: Mapped[list] = mapped_column(JSON, default=list, nullable=False)  # List[str]
    ranking_scores: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)         # Dict[str, float]

    # Relationships
    dataset_version = relationship("DatasetVersion", back_populates="feature_selection_runs")
    training_runs = relationship("TrainingRun", back_populates="feature_selection_run")
