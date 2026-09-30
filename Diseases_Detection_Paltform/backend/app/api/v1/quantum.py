"""PennyLane noiseless and noisy simulator execution endpoints."""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, status
from app.core.dependencies import get_current_user
from app.core.exceptions import AppException, ValidationError
from app.database.models.user import User
from app.quantum.registry import quantum_registry
from app.schemas.common import StandardResponse
from pydantic import BaseModel
from app.schemas.quantum import QuantumJobCreate, QuantumJobResponse

class ProviderCredentialUpdate(BaseModel):
    provider_name: str
    api_key: str

router = APIRouter(prefix="/quantum", tags=["Quantum Computing"])


@router.get("/devices")
async def list_quantum_devices(current_user: User = Depends(get_current_user)):
    """List configured PennyLane simulators; hardware is not integrated in this deployment."""
    return quantum_registry.list_devices()


@router.post("/jobs", response_model=StandardResponse[Dict[str, Any]], status_code=status.HTTP_201_CREATED)
async def submit_quantum_job(
    payload: QuantumJobCreate,
    current_user: User = Depends(get_current_user),
):
    """Execute the supplied VQC circuit inputs locally on a supported simulator."""
    if payload.device_id not in {"simulator", "noisy_simulator"}:
        raise AppException(status_code=503, code="QUANTUM_HARDWARE_UNAVAILABLE", message="Real quantum hardware execution is unavailable; no provider integration or credentials are configured.")
    backend = quantum_registry.get_backend(payload.device_id)
    circuit_config = payload.circuit_data
    try:
        import numpy as np
        n_qubits = int(circuit_config.get("n_qubits", 0))
        n_layers = int(circuit_config.get("n_layers", 0))
        values = np.asarray(circuit_config.get("features", []), dtype=float)
        weights = np.asarray(circuit_config.get("weights", []), dtype=float)
        if not backend.validate_configuration({"n_qubits": n_qubits}):
            raise ValidationError("PennyLane simulator supports at most 8 qubits.")
        if values.ndim != 1 or values.size != n_qubits:
            raise ValidationError("Circuit features must be a one-dimensional vector matching n_qubits.")
        if weights.shape != (n_layers, n_qubits):
            raise ValidationError("Trainable weights must have shape (n_layers, n_qubits).")
        encoding = str(circuit_config.get("encoding_method", "angle_ry"))
        gate = str(circuit_config.get("variational_gate", "RY"))
        entanglement = str(circuit_config.get("entanglement_strategy", "linear_cnot"))
        if encoding not in {"angle_ry", "angle_rx"} or gate not in {"RY", "RZ"} or entanglement not in {"linear_cnot", "ring_cnot", "none"}:
            raise ValidationError("Circuit configuration contains an unsupported encoding, trainable gate, or entanglement strategy.")
        if payload.device_id == "noisy_simulator":
            from app.ml.quantum.vqc.noisy import create_noisy_vqc_circuit
            noise = circuit_config.get("noise_params") or {}
            probabilities = [float(noise.get(key, default)) for key, default in (("p_gate", 0.01), ("p_cnot", 0.02), ("p_meas", 0.01))]
            if any(value < 0 or value > 0.5 for value in probabilities):
                raise ValidationError("Noise probabilities must be between 0 and 0.5.")
            circuit = create_noisy_vqc_circuit(n_qubits, n_layers, *probabilities, encoding_method=encoding, variational_gate=gate, entanglement_strategy=entanglement)
        else:
            from app.ml.quantum.vqc.circuit import create_vqc_circuit
            circuit = create_vqc_circuit(n_qubits, n_layers, encoding_method=encoding, variational_gate=gate, entanglement_strategy=entanglement)
        expectations = [float(value) for value in circuit(values, weights)]
    except ValidationError:
        raise
    except Exception as exc:
        raise ValidationError(f"PennyLane circuit execution failed: {exc}") from exc
    job_id = backend.submit_job(circuit_data=circuit_config, shots=payload.shots)
    return StandardResponse(
        message="PennyLane simulator executed the circuit successfully.",
        data={"job_id": job_id, "device_id": payload.device_id, "status": "completed", "measurement": "Pauli-Z expectation values", "expectations": expectations, "shots": "analytic"},
    )

@router.post("/credentials", response_model=StandardResponse[Dict[str, Any]])
async def update_quantum_credentials(
    payload: ProviderCredentialUpdate,
    current_user: User = Depends(get_current_user),
):
    """Reject credential writes because no provider integration or secret store exists."""
    raise AppException(
        status_code=503,
        code="QUANTUM_HARDWARE_UNAVAILABLE",
        message="Quantum provider credentials cannot be stored because hardware execution is unavailable.",
    )
