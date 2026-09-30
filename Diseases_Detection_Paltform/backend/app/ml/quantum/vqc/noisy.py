"""PennyLane Noisy NISQ Quantum Circuit matching existing repository implementation."""

import pennylane as qml
from pennylane import numpy as pnp


def create_noisy_vqc_circuit(
    n_qubits: int,
    n_layers: int = 2,
    p_gate: float = 0.01,
    p_cnot: float = 0.02,
    p_meas: float = 0.01,
    encoding_method: str = "angle_ry",
    variational_gate: str = "RY",
    entanglement_strategy: str = "linear_cnot",
):
    """Build a noisy QNode on 'default.mixed' simulator matching existing NISQ experiments.

    Noise channels:
    - DepolarizingChannel on single-qubit gates (p_gate)
    - DepolarizingChannel on two-qubit CNOT gates (p_cnot)
    - BitFlip on measurement readouts (p_meas)
    """
    dev = qml.device("default.mixed", wires=n_qubits)

    @qml.qnode(dev)
    def circuit(x, weights):
        # 1. Angle Encoding with gate noise
        encoder = qml.RY if encoding_method == "angle_ry" else qml.RX
        rotation = qml.RY if variational_gate == "RY" else qml.RZ
        for i in range(n_qubits):
            encoder(x[..., i] * pnp.pi, wires=i)
            qml.DepolarizingChannel(p_gate, wires=i)

        # 2. Variational Layers with entangling noise
        for l in range(n_layers):
            for i in range(n_qubits):
                rotation(weights[l, i], wires=i)
                qml.DepolarizingChannel(p_gate, wires=i)

            if entanglement_strategy == "linear_cnot":
                edges = [(i, i + 1) for i in range(n_qubits - 1)]
            elif entanglement_strategy == "ring_cnot" and n_qubits > 1:
                edges = [(i, i + 1) for i in range(n_qubits - 1)] + [(n_qubits - 1, 0)]
            else:
                edges = []
            for control, target in edges:
                qml.CNOT(wires=[control, target])
                qml.DepolarizingChannel(p_cnot, wires=control)
                qml.DepolarizingChannel(p_cnot, wires=target)

        # 3. Readout error channel
        for i in range(n_qubits):
            qml.BitFlip(p_meas, wires=i)

        # 4. Measurement
        return [qml.expval(qml.PauliZ(i)) for i in range(n_qubits)]

    return circuit
