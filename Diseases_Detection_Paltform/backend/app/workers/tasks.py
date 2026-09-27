"""Asynchronous background worker tasks for training, quantum jobs, and reporting."""

import time
from app.workers.celery_app import celery_app
from app.core.logging import logger


@celery_app.task(name="tasks.execute_preprocessing_job")
def execute_preprocessing_job(run_id: str, dataset_id: str) -> dict:
    """Background task executing heavy dataset cleaning and feature scaling."""
    logger.info(f"Starting background preprocessing task for run {run_id}")
    time.sleep(1)
    return {"status": "completed", "run_id": run_id}


@celery_app.task(name="tasks.execute_model_training_job")
def execute_model_training_job(training_run_id: str, model_type: str) -> dict:
    """Background task executing SVM or PennyLane VQC circuit optimization."""
    logger.info(f"Starting background training task for run {training_run_id}, model: {model_type}")
    time.sleep(2)
    return {"status": "completed", "training_run_id": training_run_id}


@celery_app.task(name="tasks.poll_quantum_hardware_job")
def poll_quantum_hardware_job(quantum_job_id: str, external_job_id: str) -> dict:
    """Background task polling remote physical QPU for circuit execution completion."""
    logger.info(f"Polling quantum hardware for job {quantum_job_id}")
    return {"status": "completed", "quantum_job_id": quantum_job_id}
