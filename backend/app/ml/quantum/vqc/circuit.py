"""PennyLane Quantum Circuit Architecture matching existing repository implementation."""

import pennylane as qml
from pennylane import numpy as pnp


def create_vqc_circuit(n_qubits: int, n_layers: int = 2, device_name: str = "default.qubit"):
    """Build a PennyLane QNode based on the existing repository's validated circuit architecture.
    
    1. Data Encoding: Angle encoding via RY(x_i * pi) on each wire i
    2. Variational Layers (n_layers):
       - Parameterized single-qubit rotations: RY(weights[l, i])
       - Entanglement: Linear chain CNOT gates between adjacent wires (0->1, 1->2, ...)
    3. Measurement: Pauli-Z expectation across all wires
    """
    dev = qml.device(device_name, wires=n_qubits)

    @qml.qnode(dev)
    def circuit(x, weights):
        # 1. Angle Encoding
        for i in range(n_qubits):
            qml.RY(x[..., i] * pnp.pi, wires=i)

        # 2. Variational Layers
        for l in range(n_layers):
            for i in range(n_qubits):
                qml.RY(weights[l, i], wires=i)
            for i in range(n_qubits - 1):
                qml.CNOT(wires=[i, i + 1])

        # 3. Measurement (Expectation of Pauli-Z on all qubits)
        return [qml.expval(qml.PauliZ(i)) for i in range(n_qubits)]

    return circuit
