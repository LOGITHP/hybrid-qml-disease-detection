"""Quantum config ODM."""
from typing import Optional, Dict, Any
from beanie import Document
from pydantic import Field
from datetime import datetime, timezone

class QuantumConfiguration(Document):
    model_id: str
    n_qubits: int = 4
    n_layers: int = 2
    ansatz: str = "strongly_entangling"
    data_encoding: str = "angle"
    backend: str = "default.qubit"
    noise_model: Optional[str] = None
    shots: Optional[int] = None
    measurement: str = "pauli_z"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "quantum_configurations"
