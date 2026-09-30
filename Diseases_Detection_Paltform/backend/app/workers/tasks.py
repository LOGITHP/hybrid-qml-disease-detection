"""Celery task names reserved for jobs not yet connected to real workers."""

from app.workers.celery_app import celery_app


@celery_app.task(name="tasks.execute_preprocessing_job")
def execute_preprocessing_job(run_id: str, dataset_id: str) -> dict:
    """Fail visibly until preprocessing is wired to a background worker."""
    raise NotImplementedError(
        "Background preprocessing is not implemented; use the synchronous preprocessing API."
    )


@celery_app.task(name="tasks.execute_model_training_job")
def execute_model_training_job(training_run_id: str, model_type: str) -> dict:
    """Fail visibly until training is wired to a background worker."""
    raise NotImplementedError(
        "Background model training is not implemented; use the synchronous training API."
    )


@celery_app.task(name="tasks.poll_quantum_hardware_job")
def poll_quantum_hardware_job(quantum_job_id: str, external_job_id: str) -> dict:
    """Fail visibly because no physical quantum hardware provider is configured."""
    raise NotImplementedError(
        "Physical quantum hardware is unavailable; only local PennyLane simulators are supported."
    )
