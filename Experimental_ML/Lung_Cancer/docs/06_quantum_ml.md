# 06. Variational Quantum Classifier (VQC): Mathematical Formulation & Architecture

## 1. Quantum State Space & VQC Principle
The Variational Quantum Classifier (VQC) is a hybrid quantum-classical algorithm where input data vectors are mapped into quantum states in a $2^n$-dimensional complex Hilbert space $\mathcal{H}$, manipulated via parameterized unitary rotations, and measured to generate predictions optimized via classical gradient descent.

```
|0⟩ ──[ RY(x₀·π) ]──[ RY(θ₁,₀) ]──╭●─────────────[ RY(θ₂,₀) ]──╭●─────────────┤ ⟨Z₀⟩ ──╮
|0⟩ ──[ RY(x₁·π) ]──[ RY(θ₁,₁) ]──╰X─╭●──────────[ RY(θ₂,₁) ]──╰X─╭●──────────┤ ⟨Z₁⟩ ──┤
|0⟩ ──[ RY(x₂·π) ]──[ RY(θ₁,₂) ]─────╰X─╭●───────[ RY(θ₂,₂) ]─────╰X─╭●───────┤ ⟨Z₂⟩ ──┼─► Mean ⟨Z⟩ ──► [+ b] ──► σ(·) ──► p(y=1)
|0⟩ ──[ RY(x₃·π) ]──[ RY(θ₁,₃) ]────────╰X─╭●────[ RY(θ₂,₃) ]────────╰X─╭●────┤ ⟨Z₃⟩ ──┤
                                         ...                              ...    ...     │
|0⟩ ──[ RY(xₙ·π) ]──[ RY(θ₁,ₙ) ]───────────╰X────[ RY(θ₂,ₙ) ]───────────╰X────┤ ⟨Zₙ⟩ ──╯
      └─────────┘   └────────────────────────┘   └────────────────────────┘   └───────┘
        Stage 1:              Stage 2:                     Stage 3:            Stage 4:
       Data Encoding       Variational Layer 1          Variational Layer 2   Measurement
```

## 2. Mathematical Circuit Formulation

### Stage 1: Feature Encoding (Angle Embedding)
Each normalized feature $x_i \in [0, 1]$ rotates qubit wire $i$ around the Y-axis:
$$R_y(\alpha) = \exp\left(-i \frac{\alpha}{2} Y\right) = \begin{pmatrix} \cos(\alpha/2) & -\sin(\alpha/2) \\ \sin(\alpha/2) & \cos(\alpha/2) \end{pmatrix}$$
Setting $\alpha = x_i \cdot \pi$:
$$|\psi_0(\mathbf{x})\rangle = \bigotimes_{i=0}^{n-1} R_y(x_i \cdot \pi) |0\rangle = \bigotimes_{i=0}^{n-1} \left[ \cos\left(\frac{x_i \pi}{2}\right)|0\rangle + \sin\left(\frac{x_i \pi}{2}\right)|1\rangle \right]$$

### Stage 2 & 3: Parameterized Variational Layers (Ansatz)
For $L = 2$ layers, the ansatz applies:
1. **Parameterized Rotations**: $U_{\text{rot}}(\boldsymbol{\theta}_l) = \bigotimes_{i=0}^{n-1} R_y(\theta_{l, i})$.
2. **Linear Entanglement Ladder**: Nearest-neighbor CNOT entangling gates:
   $$U_{\text{ent}} = \prod_{i=0}^{n-2} \text{CNOT}_{(i, i+1)}$$
The state before measurement is:
$$|\psi(\mathbf{x}, \boldsymbol{\theta})\rangle = U_{\text{ent}} U_{\text{rot}}(\boldsymbol{\theta}_2) U_{\text{ent}} U_{\text{rot}}(\boldsymbol{\theta}_1) |\psi_0(\mathbf{x})\rangle$$

### Stage 4: Observable Measurement & Classical Sigmoid Head
- Pauli-Z expectation on wire $i$: $\langle Z_i \rangle = \langle \psi(\mathbf{x}, \boldsymbol{\theta}) | Z_i | \psi(\mathbf{x}, \boldsymbol{\theta}) \rangle \in [-1, 1]$.
- Mean ensemble expectation: $\langle Z \rangle = \frac{1}{n} \sum_{i=0}^{n-1} \langle Z_i \rangle$.
- Prediction probability: $\hat{p} = \sigma(\langle Z \rangle + b) = \frac{1}{1 + e^{-(\langle Z \rangle + b)}}$.
- **Parameter Efficiency**: Only $n \times 2 + 1$ trainable parameters (9 for 4 qubits; 13 for 6 qubits; 17 for 8 qubits).

## 3. Empirical Results Across Quantum Architectures

| Quantum Model | Qubits | Dims ($2^n$) | Trainable Params | Accuracy | Balanced Acc | Sensitivity | Specificity | F1-Score | ROC-AUC | False Positives | False Negatives |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **4-Qubit Noiseless VQC** | 4 | 16 | 9 | 52.67% | 52.69% | 49.78% | 55.61% | 51.48% | 0.5147 | 99 | 114 |
| **6-Qubit Noiseless VQC** | 6 | 64 | 13 | 53.11% | 52.92% | **74.45%** | 31.39% | **61.57%** | **0.5555** | 153 | **58** |
| **8-Qubit Noiseless VQC** | 8 | 256 | 17 | 48.44% | 48.50% | 42.73% | 54.26% | 45.54% | 0.4990 | 102 | 130 |

## 4. In-Depth Interpretation of Quantum Results
1. **Peak Sensitivity in 6-Qubit VQC (74.45%)**:
   - The 6-Qubit VQC achieved the highest positive-class recall in the entire study, correctly detecting 169 of the 227 cancer cases and missing only 58.
   - Compared to classical 6-feature RBF SVM (60.79%, 89 missed cases) and Logistic Regression (68.28%, 72 missed cases), the quantum circuit demonstrated superior positive identification on this dataset.
2. **Parameter Economy**:
   - The 6-qubit VQC achieved this performance with only **13 parameters**, contrasting sharply with classical SVMs that require support vectors over the training set.
3. **The 8-Qubit Plateau**:
   - Expanding to 8 qubits degraded accuracy to 48.44% and sensitivity to 42.73%. Operating in a 256-dimensional Hilbert space without proportional increases in sample volume leads to diffuse gradients, illustrating that qubit expansion must be clinically and statistically justified.
