"""Quantum Provider and Device Registry supporting Simulator, Noisy Simulator, and Physical Hardware."""

from typing import Any, Dict, List
from app.core.exceptions import AppException
from app.interfaces.quantum import IQuantumBackend


class SimulatorQuantumBackend(IQuantumBackend):
    """PennyLane standard statevector simulator backend."""

    def __init__(self, num_qubits: int = 4):
        self.num_qubits = num_qubits

    def get_device_info(self) -> Dict[str, Any]:
        return {
            "device_id": "simulator",
            "name": "PennyLane Statevector Simulator",
            "device_type": "simulator",
            "num_qubits": self.num_qubits,
            "qubits": self.num_qubits,
            "provider": "PennyLane",
            "is_available": True,
            "status": "ONLINE",
            "shots_supported": [],
            "average_queue_time_seconds": 0,
        }

    def validate_configuration(self, circuit_config: Dict[str, Any]) -> bool:
        required_qubits = circuit_config.get("n_qubits", 4)
        return required_qubits <= self.num_qubits

    def run(self, circuit_func: Any, shots: int = 1000, **kwargs: Any) -> Any:
        return circuit_func(**kwargs)

    def submit_job(self, circuit_data: Dict[str, Any], shots: int = 1000) -> str:
        # Simulator executes instantly; generate job ID
        import uuid
        return f"sim-job-{uuid.uuid4().hex[:12]}"

    def get_job_status(self, job_id: str) -> str:
        return "completed"

    def get_job_result(self, job_id: str) -> Dict[str, Any]:
        return {"status": "completed", "shots": 1000, "info": "Statevector simulation finished"}

    def cancel_job(self, job_id: str) -> bool:
        return True


class NoisySimulatorQuantumBackend(IQuantumBackend):
    """PennyLane mixed-state open quantum system simulator with customizable noise."""

    def __init__(self, num_qubits: int = 4, p_gate: float = 0.01, p_cnot: float = 0.02, p_meas: float = 0.01):
        self.num_qubits = num_qubits
        self.p_gate = p_gate
        self.p_cnot = p_cnot
        self.p_meas = p_meas

    def get_device_info(self) -> Dict[str, Any]:
        return {
            "device_id": "noisy_simulator",
            "name": "PennyLane Noisy Mixed-State Simulator",
            "device_type": "noisy_simulator",
            "num_qubits": self.num_qubits,
            "qubits": self.num_qubits,
            "provider": "PennyLane",
            "is_available": True,
            "status": "ONLINE",
            "shots_supported": [],
            "average_queue_time_seconds": 0,
            "noise_model": {
                "p_gate": self.p_gate,
                "p_cnot": self.p_cnot,
                "p_meas": self.p_meas,
            },
        }

    def validate_configuration(self, circuit_config: Dict[str, Any]) -> bool:
        required_qubits = circuit_config.get("n_qubits", 4)
        return required_qubits <= self.num_qubits

    def run(self, circuit_func: Any, shots: int = 1000, **kwargs: Any) -> Any:
        return circuit_func(**kwargs)

    def submit_job(self, circuit_data: Dict[str, Any], shots: int = 1000) -> str:
        import uuid
        return f"noisy-sim-job-{uuid.uuid4().hex[:12]}"

    def get_job_status(self, job_id: str) -> str:
        return "completed"

    def get_job_result(self, job_id: str) -> Dict[str, Any]:
        return {"status": "completed", "shots": 1000, "info": "Noisy mixed-state simulation finished"}

    def cancel_job(self, job_id: str) -> bool:
        return True


class QuantumRegistry:
    """Register only the PennyLane simulator backends supported by this platform."""

    def __init__(self):
        self._backends: Dict[str, IQuantumBackend] = {
            "simulator": SimulatorQuantumBackend(num_qubits=8),
            "noisy_simulator": NoisySimulatorQuantumBackend(num_qubits=8),
        }

    def get_backend(self, name: str) -> IQuantumBackend:
        if name not in self._backends:
            raise AppException(
                status_code=404,
                code="QUANTUM_BACKEND_NOT_FOUND",
                message=f"Quantum backend '{name}' not found. Supported backends: {list(self._backends.keys())}",
            )
        return self._backends[name]

    def list_devices(self) -> List[Dict[str, Any]]:
        return [backend.get_device_info() for backend in self._backends.values()]


quantum_registry = QuantumRegistry()
