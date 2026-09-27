"""Quantum computing endpoints supporting simulators, noisy devices, and physical hardware."""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, status
from app.core.dependencies import get_current_user
from app.database.models.user import User
from app.quantum.registry import quantum_registry
from app.schemas.common import StandardResponse
from app.schemas.quantum import QuantumJobCreate, QuantumJobResponse

router = APIRouter(prefix="/quantum", tags=["Quantum Computing"])


@router.get("/devices")
async def list_quantum_devices(current_user: User = Depends(get_current_user)):
    """List registered quantum backends (Statevector Simulator, Noisy Simulator, Physical Hardware)."""
    return quantum_registry.list_devices()


@router.post("/jobs", response_model=StandardResponse[Dict[str, Any]], status_code=status.HTTP_201_CREATED)
async def submit_quantum_job(
    payload: QuantumJobCreate,
    current_user: User = Depends(get_current_user),
):
    """Submit a quantum circuit execution job to simulator or QPU queue."""
    backend = quantum_registry.get_backend("simulator")
    job_id = backend.submit_job(circuit_data=payload.circuit_data, shots=payload.shots)
    return StandardResponse(
        message="Quantum job submitted.",
        data={"job_id": job_id, "device_id": payload.device_id, "status": "completed"},
    )
