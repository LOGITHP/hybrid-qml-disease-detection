# 10. Platform Architecture: Research Modularity & Extensibility

## 1. Architectural Design Principles
The repository enforces a clean architectural separation between scientific research and future deployment layers:

```
Experimental_ML/
└── Lung_Cancer/
    ├── data/          <- Raw and preprocessed data partitions
    ├── notebooks/     <- Step-by-step reproducible research notebooks
    ├── CML/           <- Classical machine learning (4, 6, 8 features)
    ├── HQML/          <- Hybrid quantum classification (4, 4-noisy, 6, 8 qubits)
    ├── results/       <- Consolidated benchmarks and comparisons
    └── docs/          <- Methodological documentation
```

## 2. Decoupling from Future Production Services
1. **No Mixed Platform Code**:
   Backend microservices (FastAPI), databases (PostgreSQL), and web frontends (React/Next.js) are explicitly decoupled from `Experimental_ML/`.
2. **Self-Contained Reproducibility**:
   Every experiment directory (`CML/4-feature/`, `HQML/6-feature-VQC/`) possesses its own dedicated training script, saved model artifacts, metrics, and explanatory README.
3. **Multi-Disease Extensibility**:
   While the current experimental focus is Lung Cancer, the hierarchical directory design (`Experimental_ML/<Disease_Name>/...`) enables seamless future onboarding of additional pathologies (e.g., Breast Cancer, Diabetes) following identical data and quantum engineering protocols.
