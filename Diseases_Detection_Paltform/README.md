# Hybrid Quantum Machine Learning Platform for Early Disease Detection

## Project Overview

This repository contains the complete implementation for the **Hybrid Quantum Machine Learning Platform for Early Disease Detection**, with an initial focus on early lung cancer detection using biomedical datasets. The platform fundamentally modernizes disease prediction by coupling robust classical Machine Learning preprocessing and models (SVMs, Random Forests) with cutting-edge Variational Quantum Classifiers (VQC) using PennyLane. 

The architecture is designed as a highly scalable, containerized microservices platform utilizing a modern stack:
- **Backend**: FastAPI, MongoDB (Beanie ODM), MinIO, Celery, Redis
- **Frontend**: React, TypeScript, Vite, TailwindCSS
- **Quantum & ML**: PennyLane, Scikit-Learn, Pandas, Numpy
- **LLM Agent**: Ollama (Local Large Language Models) for intelligent data preprocessing recommendations and explainability.

## Repository Structure

```text
hybrid-qml-disease-detection/
├── ai_preprocessing_agent/   # Standalone Python package for LLM-powered schema parsing & plan generation
├── Diseases_Detection_Platform/
│   ├── backend/                  # FastAPI microservice for ML & Quantum computation
│   │   ├── app/                  # Application source code
│   │   │   ├── api/v1/           # RESTful API Endpoints
│   │   │   ├── core/             # Configuration, dependencies, and security
│   │   │   ├── database/         # MongoDB (Beanie) ODM Models and Session management
│   │   │   ├── ml/               # Classical ML pipelines (PCA, SVM, Imputation)
│   │   │   ├── quantum/          # PennyLane VQC architecture (Ansatz, Angle Embedding)
│   │   │   ├── repositories/     # Data Access Layer
│   │   │   ├── schemas/          # Pydantic validation schemas
│   │   │   └── services/         # Business logic layer
│   │   ├── tests/                # Pytest suite
│   │   ├── Dockerfile            # Backend container configuration
│   │   └── requirements.txt      # Python dependencies
│   ├── frontend/                 # React & Vite SPA UI
│   │   ├── src/                  # UI source code
│   │   │   ├── api/              # Axios API clients
│   │   │   ├── components/       # Reusable UI components (Charts, Forms, CircuitDesigner)
│   │   │   ├── pages/            # View components (Dashboard, Datasets, Models)
│   │   │   ├── store/            # Zustand global state management
│   │   │   └── styles/           # Tailwind and global CSS
│   │   ├── Dockerfile            # Frontend container (Nginx)
│   │   └── package.json          # Node dependencies
│   ├── docker-compose.yml        # Orchestrates MongoDB, Redis, MinIO, Ollama, Backend, Frontend
│   └── README.md                 # Project documentation
```

## Platform Accomplishments & Model Comparison

In building this platform, we established a rigorous benchmark comparing classical learning against quantum-enhanced learning:

1. **Data Handling & Preprocessing**: We developed a robust data ingestion pipeline capable of parsing tabular biomedical data. The pipeline leverages a localized Ollama LLM Agent to automatically recommend feature engineering strategies (handling missing values, standard scaling, and PCA).
2. **Classical Baseline**: We implemented a Classical Support Vector Machine (SVM) and Random Forest classifier to serve as our baseline benchmark on the lung cancer datasets.
3. **Variational Quantum Classifier (VQC)**: We constructed a parameterized quantum circuit using PennyLane (`default.qubit` simulator). The VQC utilizes Angle Embedding to map classical features into a high-dimensional Hilbert space, followed by Strongly Entangling Layers to train the model. 
4. **Model Comparison**: 
   - *Classical SVM* excels at rapid convergence and high baseline accuracy on linearly separable biomedical features.
   - *Quantum VQC* demonstrates superior feature expressivity, specifically capturing complex, non-linear correlations in the patient data. Our hybrid approach shows promising theoretical advantages in parameter efficiency.
5. **Zero Data Leakage Architecture**: Strict temporal and logical separation of training and testing data splits are enforced at the database level to ensure clinical validity.

## Recent Updates & Fixes

We have recently improved the robustness and UX of the training and model management pipeline:
- **GPU-Accelerated Quantum Simulation**: The platform now enforces PennyLane's `lightning.gpu` (cuQuantum) simulator for VQC models by default when available, vastly speeding up circuit execution times for biomedical datasets.
- **Improved UI and Session State**: Fixed an issue in the Training Wizard where stale dataset UUIDs were cached in `sessionStorage` and sent to the backend, causing 404 crashes. The UI now auto-clears stale state and securely ties downstream runs to validated Dataset Versions.
- **Model Zoo Clarity**: Redesigned the Model Zoo page to display human-readable dataset names and version tags in the filter dropdowns and Model Cards instead of raw MongoDB Object IDs.
- **System Dataset Permissions**: Fixed an authorization bug in `training_service.py` that inadvertently blocked users from training models on system-seeded datasets (e.g., the default Lung Cancer benchmark dataset).
- **Background Task Resilience**: Wrapped Celery/FastAPI `BackgroundTasks` with global exception handlers. If a training run crashes (e.g., due to OOM errors or invalid configs), it is caught and safely marked as `failed` in the database, preventing "zombie" runs.

## How to Run (Docker Compose)


The entire platform is heavily containerized. You do not need to install local databases or Python environments.

1. Ensure **Docker** and **Docker Compose** are installed and running on your system.
2. Navigate to the root directory (`Diseases_Detection_Platform`).
3. Run the complete stack in detached mode:
   ```bash
   docker compose up --build -d
   ```
4. **Services Mapping**:
   - Frontend UI: `http://localhost:3000`
   - Backend API Docs (Swagger): `http://localhost:8000/api/v1/docs`
   - MinIO Console: `http://localhost:9001` (Credentials: minioadmin / minioadmin)
   - MongoDB: `localhost:27017`

To shut down the platform:
```bash
docker compose down
```

## Troubleshooting

- **Large Dataset Upload Failures (Timeout or `413 Request Entity Too Large`)**:
  The application Nginx proxy has been configured to accept bodies up to 100MB, and the frontend Axios client timeout is set to 5 minutes (300,000ms). If uploads fail or time out, verify your Docker Engine resources and network settings.
- **Docker Compose Build Failures (`no such host`)**:
  If a step fails with a DNS resolution error fetching from Docker Hub (e.g., `registry-1.docker.io`), this is a transient Docker networking issue. Retry the build step.
