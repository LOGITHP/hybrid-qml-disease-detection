"""Evaluation run ORM model."""

from typing import Optional
from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class EvaluationRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Model evaluation record storing benchmark metrics and comparative results."""

    __tablename__ = "evaluation_runs"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    model_version_id: Mapped[str] = mapped_column(ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_version_id: Mapped[str] = mapped_column(ForeignKey("dataset_versions.id", ondelete="CASCADE"), nullable=False, index=True)

    status: Mapped[str] = mapped_column(String(50), default="completed", nullable=False)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)  # accuracy, precision, recall, f1, roc_auc, cm
    report_artifact_id: Mapped[Optional[str]] = mapped_column(ForeignKey("artifacts.id", ondelete="SET NULL"), nullable=True)
