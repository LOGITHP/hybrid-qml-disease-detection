from typing_extensions import Annotated
"""Quantum device, provider, and execution job schemas."""

from datetime import datetime
from typing import Any, Dict, Literal, Optional
from pydantic import BeforeValidator, BaseModel, Field


class QuantumProviderResponse(BaseModel):
    """Quantum hardware or cloud simulation vendor."""
    id: Annotated[str, BeforeValidator(str)]
    name: str
    description: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class QuantumDeviceResponse(BaseModel):
    """Specific quantum simulator or physical QPU device."""
    id: Annotated[str, BeforeValidator(str)]
    provider_id: str
    name: str
    device_type: Literal["simulator", "noisy_simulator", "hardware"]
    num_qubits: int
    is_available: bool
    config: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class QuantumJobCreate(BaseModel):
    """Submit a quantum circuit execution job."""
    device_id: str
    training_run_id: Optional[str] = None
    shots: int = Field(default=1000, ge=1, le=100000)
    circuit_data: Dict[str, Any] = Field(default_factory=dict)


class QuantumJobResponse(BaseModel):
    """Status and measurement outcomes of a quantum circuit job."""
    id: Annotated[str, BeforeValidator(str)]
    user_id: str
    device_id: str
    training_run_id: Optional[str] = None
    external_job_id: Optional[str] = None
    status: str
    shots: int
    circuit_data: Dict[str, Any]
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    submitted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
