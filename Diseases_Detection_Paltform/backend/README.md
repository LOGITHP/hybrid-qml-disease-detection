# Backend API - Hybrid Quantum Machine Learning Platform

The backend of the Hybrid QML Platform is a high-performance Python application built with **FastAPI**. It handles complex computational workloads including classical data preprocessing, machine learning, quantum circuit simulation (PennyLane), and intelligent agent interaction.

## Architecture & Tech Stack

- **Framework**: FastAPI (Asynchronous, High Concurrency)
- **Database**: MongoDB (Beanie ODM) for flexible document storage of models, datasets, and configurations.
- **Storage Engine**: MinIO (S3-compatible) for storing massive CSV files, serialized ML pipelines, and model weights.
- **Task Queue**: Celery + Redis for asynchronous background processing (model training, quantum simulation).
- **Quantum Backend**: PennyLane (`default.qubit`) for Variational Quantum Classifier construction and simulation.
- **LLM Engine**: Ollama (Local LLM) used dynamically by LangChain agents to suggest data preprocessing steps without sending patient data to cloud providers.

## Implementation Details

The backend adheres to a strict Service-Oriented Architecture (SOA):

1. **API Layer (`app/api/`)**: Defines REST endpoints, handles HTTP requests/responses, and enforces Pydantic schema validation.
2. **Service Layer (`app/services/`)**: Contains the core business logic. API routes inject these services via FastAPI Dependencies.
3. **Repository Layer (`app/repositories/`)**: Abstracts database queries. Directly interfaces with the Beanie ODM to isolate MongoDB logic.
4. **Machine Learning (`app/ml/` & `app/quantum/`)**: Pure Python modules wrapping Scikit-Learn and PennyLane logic to ensure models remain decoupled from the web framework.

### Step-by-Step Execution Flow

1. **Dataset Upload**: The user uploads a CSV. The API streams it directly to MinIO, and a `DatasetVersion` document is saved in MongoDB.
2. **Preprocessing**: The `PreprocessingService` queries Ollama to analyze dataset headers and suggest Imputation (Mean/Median) and Scaling (Standard/MinMax). The dataset is processed using Scikit-Learn pipelines, and the transformer artifacts are saved to MinIO.
3. **Quantum Model Configuration**: The user configures a VQC model (number of qubits, ansatz type).
4. **Training**: A Celery worker picks up the training job. It pulls the processed dataset from MinIO, constructs a PennyLane quantum circuit, and trains it using an optimizer (e.g., Adam/Adagrad). Training history is streamed back to MongoDB.
5. **Evaluation & Prediction**: The trained model generates predictions and Explainable AI (XAI) metrics, storing results as an `Evaluation` document.

## Configuration (.env)

When running locally without Docker, you must configure a `.env` file in the `backend/` directory:

```env
ENVIRONMENT=development
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=hybrid_qml_db
REDIS_URL=redis://localhost:6379/0
MINIO_URL=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
JWT_SECRET=your_super_secret_key
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434
```

## How to Run (With Docker)

The backend is configured to be orchestrated entirely by Docker Compose from the root directory.

However, if you want to build and run *only* the backend container:

```bash
cd backend
docker build -t hybrid_qml_backend .
docker run -p 8000:8000 --env-file .env hybrid_qml_backend
```

Note: Running the backend in isolation requires MongoDB, Redis, MinIO, and Ollama to be accessible at the URLs specified in your `.env` file.
