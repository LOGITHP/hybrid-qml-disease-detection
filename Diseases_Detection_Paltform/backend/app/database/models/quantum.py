"""Quantum provider, device, and asynchronous job execution ORM models."""

from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class QuantumProvider(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Quantum hardware or cloud simulation service provider."""

    __tablename__ = "quantum_providers"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    devices = relationship("QuantumDevice", back_populates="provider", cascade="all, delete-orphan")


class QuantumDevice(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Specific quantum processing unit (QPU) or state-vector simulator."""

    __tablename__ = "quantum_devices"

    provider_id: Mapped[str] = mapped_column(ForeignKey("quantum_providers.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    device_type: Mapped[str] = mapped_column(String(50), nullable=False)  # simulator, noisy_simulator, hardware
    num_qubits: Mapped[int] = mapped_column(Integer, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    provider = relationship("QuantumProvider", back_populates="devices")
    jobs = relationship("QuantumJob", back_populates="device")


class QuantumJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Execution instance of a quantum circuit or batch job."""

    __tablename__ = "quantum_jobs"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id: Mapped[str] = mapped_column(ForeignKey("quantum_devices.id", ondelete="RESTRICT"), nullable=False, index=True)
    training_run_id: Mapped[Optional[str]] = mapped_column(ForeignKey("training_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    external_job_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # created, queued, submitted, running, completed, failed, cancelled
    status: Mapped[str] = mapped_column(String(50), default="created", nullable=False)
    shots: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    circuit_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    results: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    device = relationship("QuantumDevice", back_populates="jobs")
