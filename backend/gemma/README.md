# Dedicated Gemma LLM Microservice

This microservice runs as an isolated container in Docker Compose to handle clinical reasoning and AI preprocessing plan formulation.

## Isolation Guarantees
- The Gemma container runs independently from the FastAPI backend.
- It is reachable strictly over the internal Docker network (`http://gemma:8001`).
- The frontend CANNOT communicate directly with Gemma.
- The LLM does NOT execute arbitrary Python code, shell commands, or SQL queries.
- Raw biomedical patient datasets are never transmitted to this service; only anonymized statistical profiles (row counts, column types, missingness) are sent for recommendation synthesis.
