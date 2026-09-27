"""Prediction run ORM model."""

from typing import Optional
from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PredictionRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Inference execution using a trained model version and associated pipeline."""

    __tablename__ = "prediction_runs"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    model_version_id: Mapped[str] = mapped_column(ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    preprocessing_run_id: Mapped[Optional[str]] = mapped_column(ForeignKey("preprocessing_runs.id", ondelete="SET NULL"), nullable=True)
    feature_selection_run_id: Mapped[Optional[str]] = mapped_column(ForeignKey("feature_selection_runs.id", ondelete="SET NULL"), nullable=True)

    # queued, running, completed, failed
    status: Mapped[str] = mapped_column(String(50), default="queued", nullable=False)
    input_artifact_id: Mapped[Optional[str]] = mapped_column(ForeignKey("artifacts.id", ondelete="SET NULL"), nullable=True)
    output_artifact_id: Mapped[Optional[str]] = mapped_column(ForeignKey("artifacts.id", ondelete="SET NULL"), nullable=True)
    predictions_summary: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
