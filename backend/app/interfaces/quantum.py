"""Quantum execution backend interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class IQuantumBackend(ABC):
    """Abstract interface for quantum computing execution backends (Simulator, Noisy, Hardware)."""

    @abstractmethod
    def get_device_info(self) -> Dict[str, Any]:
        """Return device metadata, qubit capacity, topology, and noise parameters."""
        pass

    @abstractmethod
    def validate_configuration(self, circuit_config: Dict[str, Any]) -> bool:
        """Validate whether the circuit configuration matches device capabilities."""
        pass

    @abstractmethod
    def run(self, circuit_func: Any, shots: int = 1000, **kwargs: Any) -> Any:
        """Execute a quantum circuit synchronously on a local or remote simulator."""
        pass

    @abstractmethod
    def submit_job(self, circuit_data: Dict[str, Any], shots: int = 1000) -> str:
        """Submit circuit for asynchronous execution on remote hardware or queue. Returns external job ID."""
        pass

    @abstractmethod
    def get_job_status(self, job_id: str) -> str:
        """Query job status (queued, running, completed, failed, cancelled)."""
        pass

    @abstractmethod
    def get_job_result(self, job_id: str) -> Dict[str, Any]:
        """Retrieve measurement outcomes or expectation values for a completed job."""
        pass

    @abstractmethod
    def cancel_job(self, job_id: str) -> bool:
        """Cancel an ongoing or queued quantum job."""
        pass
