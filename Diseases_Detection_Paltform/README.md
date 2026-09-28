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
Diseases_Detection_Platform/
├── backend/                  # FastAPI microservice for ML & Quantum computation
│   ├── app/                  # Application source code
│   │   ├── agents/           # LLM-powered preprocessing and explanation agents
│   │   ├── api/v1/           # RESTful API Endpoints
│   │   ├── core/             # Configuration, dependencies, and security
│   │   ├── database/         # MongoDB (Beanie) ODM Models and Session management
│   │   ├── ml/               # Classical ML pipelines (PCA, SVM, Imputation)
│   │   ├── quantum/          # PennyLane VQC architecture (Ansatz, Angle Embedding)
│   │   ├── repositories/     # Data Access Layer
│   │   ├── schemas/          # Pydantic validation schemas
│   │   └── services/         # Business logic layer
│   ├── tests/                # Pytest suite
│   ├── Dockerfile            # Backend container configuration
│   └── requirements.txt      # Python dependencies
├── frontend/                 # React & Vite SPA UI
│   ├── src/                  # UI source code
│   │   ├── api/              # Axios API clients
│   │   ├── components/       # Reusable UI components (Charts, Forms)
│   │   ├── pages/            # View components (Dashboard, Datasets, Models)
│   │   ├── store/            # Zustand global state management
│   │   └── styles/           # Tailwind and global CSS
│   ├── Dockerfile            # Frontend container (Nginx)
│   └── package.json          # Node dependencies
├── docker-compose.yml        # Orchestrates MongoDB, Redis, MinIO, Ollama, Backend, Frontend
└── README.md                 # Project root documentation
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

## How to Run (Docker Compose)

The entire platform is heavily containerized. You do not need to install local databases or Python environments.

1. Ensure **Docker** and **Docker Compose** are installed and running on your system.
2. Navigate to the root directory (`Diseases_Detection_Platform`).
3. Run the complete stack in detached mode:
   ```bash
   docker-compose up --build -d
   ```
4. **Services Mapping**:
   - Frontend UI: `http://localhost:3000`
   - Backend API Docs (Swagger): `http://localhost:8000/api/v1/docs`
   - MinIO Console: `http://localhost:9001` (Credentials: minioadmin / minioadmin)
   - MongoDB: `localhost:27017`

To shut down the platform:
```bash
docker-compose down
```
