# VQC Circuit Configuration Implementation

## Accomplished Tasks
1. **Data encoding**: Added support for angle encoding (`angle_ry` and `angle_rx`).
2. **Number of qubits**: Exposed an input field to configure `n_qubits` (1 to 8).
3. **Feature-to-qubit mapping**: Included a visual layout mapping selected features to qubits (`feature` to `qX`).
4. **Variational layers & Number of layers**: Added configuration for `n_layers` (1 to 10).
5. **Trainable gates**: Added selection between `RY` and `RZ` gates for the parameterized layers.
6. **Entanglement strategy**: Implemented `linear_cnot`, `ring_cnot`, and `none` for entanglement layer options.
7. **Measurement strategy**: Clarified measurement strategy via Pauli-Z expectation pooling by mean in the UI and backend implementation.
8. **Circuit depth**: Supported in the PennyLane backend spec analysis and visually represented via the `CircuitDesigner` component.
9. **Noise**: Integrated `default.qubit` (noiseless) and `default.mixed` (noisy) with explicit configuration for `p_gate`, `p_cnot`, and `p_meas`.
10. **Execution backend**: Implemented selector to choose between *noiseless simulator*, *noisy simulator*, and *real quantum hardware* (mocked fallback in the backend, but properly saved in configuration).
11. **Serialization**: Updated backend `training_service.py` to correctly extract and store `backend_type` dynamically instead of overwriting it when real hardware is selected. The `quantum_config` dictionary is properly appended to `model.configuration` for serialization alongside trained models.

All updates were seamlessly integrated into the `VQCConfigPage.tsx` interface and the PennyLane training loops in `training_service.py`.
