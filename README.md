# Hybrid Quantum Machine Learning Platform for Early Disease Detection

This repository contains the end-to-end platform for the Smart India Hackathon (SIH) project:
**"Hybrid Quantum Machine Learning Platform for Early Disease Detection"**

---

## Repository Structure

- **`backend/`**: Complete production-grade FastAPI application, database schemas, model registries, PennyLane quantum abstractions, Gemma AI preprocessing agent integration, and Dockerized deployment. See [`backend/README.md`](file:///backend/README.md).
- **`Experimental_ML/`**: Research, exploratory data analysis, and benchmark training pipelines for Lung Cancer screening using Classical ML (SVM Linear, SVM RBF) and Variational Quantum Classifiers (VQC 4, 6, 8-qubit).
- **`ai_preprocessing_agent/`**: Standalone research module for LLM-assisted clinical data preprocessing, automated quality auditing, and feature engineering.
- **`Experiment_Training_With_Cancer_Data_Set/`**: Historical experimental runs and preliminary prototypes.

---

## Quickstart

For local development and containerized deployment with Docker Compose:

```bash
cd backend
docker-compose up --build -d
```

Access the interactive API documentation at `http://localhost:8000/api/v1/docs`.
