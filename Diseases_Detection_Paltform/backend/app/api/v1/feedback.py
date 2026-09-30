"""Persist prediction feedback and manually create versioned retraining candidates."""

import io
from datetime import datetime, timezone
from typing import List

import joblib
import pandas as pd
from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_current_user
from app.database.models import (
    Dataset,
    DatasetVersion,
    FeatureSelectionRun,
    Model,
    Prediction,
    PredictionFeedback,
    PreprocessingArtifact,
    PreprocessingRun,
    TrainingRun,
    User,
)
from app.schemas import StandardResponse, FeedbackCreate, FeedbackResponse, FeedbackStats, TrainingRunResponse
from app.schemas.preprocessing import PreprocessingPlan, PreprocessingPlanStep
from app.services.artifact_service import artifact_storage
from app.services.training_service import TrainingService

router = APIRouter(prefix="/feedback", tags=["Feedback & Retraining"])


async def _get_owned_model(model_id: str, user: User) -> Model:
    try:
        model = await Model.get(PydanticObjectId(model_id))
    except Exception:
        model = None
    if not model or (model.user_id != str(user.id) and not model.is_default and user.role != "admin"):
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.post("", response_model=StandardResponse[FeedbackResponse])
async def submit_feedback(request: FeedbackCreate, current_user: User = Depends(get_current_user)):
    """Attach verified feedback to a persisted prediction owned by this user."""
    try:
        prediction = await Prediction.get(PydanticObjectId(request.prediction_id))
    except Exception:
        prediction = None
    if not prediction or prediction.user_id != str(current_user.id):
        raise HTTPException(status_code=404, detail="Prediction not found")
    if prediction.model_id != request.model_id:
        raise HTTPException(status_code=422, detail="Feedback model does not match the saved prediction.")
    model = await _get_owned_model(request.model_id, current_user)
    if model.status != "trained" or not prediction.dataset_version_id:
        raise HTTPException(status_code=422, detail="Feedback requires a trained model with an available associated dataset version.")

    if request.is_correct:
        verified_label = int(prediction.prediction_result)
    else:
        if request.verified_label not in (0, 1):
            raise HTTPException(status_code=422, detail="Incorrect predictions require a verified binary label (0 or 1).")
        if request.verified_label == int(prediction.prediction_result):
            raise HTTPException(status_code=422, detail="The verified label must differ from the predicted class when marked incorrect.")
        verified_label = int(request.verified_label)

    feedback = PredictionFeedback(
        prediction_id=str(prediction.id),
        model_id=str(model.id),
        user_id=str(current_user.id),
        reviewer_id=str(current_user.id),
        model_version=str((model.configuration or {}).get("model_version", model.id)),
        is_correct=request.is_correct,
        verified_label=verified_label,
        original_input=dict(prediction.input_data or {}),
        notes=request.notes,
        status="pending",
    )
    await feedback.insert()
    return StandardResponse(data=FeedbackResponse.model_validate(feedback), message="Verified feedback saved for manual review.")


@router.get("/model/{model_id}", response_model=StandardResponse[List[FeedbackResponse]])
async def list_model_feedback(model_id: str, current_user: User = Depends(get_current_user)):
    await _get_owned_model(model_id, current_user)
    feedbacks = await PredictionFeedback.find(
        PredictionFeedback.model_id == model_id,
        PredictionFeedback.user_id == str(current_user.id),
    ).to_list()
    return StandardResponse(data=[FeedbackResponse.model_validate(item) for item in feedbacks])


@router.get("/model/{model_id}/stats", response_model=StandardResponse[FeedbackStats])
async def get_feedback_stats(model_id: str, current_user: User = Depends(get_current_user)):
    await _get_owned_model(model_id, current_user)
    feedbacks = await PredictionFeedback.find(
        PredictionFeedback.model_id == model_id,
        PredictionFeedback.user_id == str(current_user.id),
    ).to_list()
    total = len(feedbacks)
    correct = sum(1 for item in feedbacks if item.is_correct)
    pending = sum(1 for item in feedbacks if item.status == "pending" and item.verified_label in (0, 1))
    stats = FeedbackStats(
        total_feedback=total,
        correct_predictions=correct,
        incorrect_predictions=total - correct,
        clinician_accuracy=(correct / total) if total else 0.0,
        pending_retrain_count=pending,
    )
    return StandardResponse(data=stats)


@router.post("/model/{model_id}/retrain", response_model=StandardResponse[TrainingRunResponse])
async def retrain_on_feedback(model_id: str, current_user: User = Depends(get_current_user)):
    """Create a new candidate from the original cohort plus verified feedback; never replace/deploy the parent."""
    model = await _get_owned_model(model_id, current_user)
    config = model.configuration or {}
    source_version_id = config.get("dataset_version_id") or model.dataset_version_id
    target_column = config.get("target_column")
    selected_features = list(config.get("selected_features") or model.selected_features_snapshot or [])
    source_preprocessing_id = config.get("preprocessing_run_id") or model.preprocessing_run_id
    source_feature_run_id = config.get("feature_selection_run_id") or model.feature_selection_run_id
    if not source_version_id or not target_column or not selected_features:
        raise HTTPException(status_code=400, detail="This model is missing its source dataset, target, or feature lineage and cannot be retrained.")

    source_version = await DatasetVersion.get(PydanticObjectId(source_version_id))
    if not source_version or source_version.user_id != str(current_user.id):
        raise HTTPException(status_code=404, detail="Dataset unavailable — retraining requires the model's original dataset version.")
    source_dataset = await Dataset.get(PydanticObjectId(source_version.dataset_id))
    if not source_dataset or source_dataset.user_id != str(current_user.id):
        raise HTTPException(status_code=404, detail="Dataset unavailable — retraining requires the model's original dataset.")

    feedbacks = await PredictionFeedback.find(
        PredictionFeedback.model_id == model_id,
        PredictionFeedback.user_id == str(current_user.id),
        PredictionFeedback.status == "pending",
    ).to_list()
    feedbacks = [item for item in feedbacks if item.verified_label in (0, 1)]
    if not feedbacks:
        raise HTTPException(status_code=400, detail="No verified pending feedback is available for retraining.")

    artifact_path = f"models/{model.id}/model.joblib"
    if not artifact_storage.exists(artifact_path):
        raise HTTPException(status_code=404, detail="The model artifact is unavailable; retraining cannot continue.")
    bundle = joblib.load(io.BytesIO(artifact_storage.load(artifact_path)))
    target_mapping = bundle.get("target_mapping") or {}
    inverse_target_mapping = {int(label): raw for raw, label in target_mapping.items()}
    if set(inverse_target_mapping) != {0, 1}:
        raise HTTPException(status_code=422, detail="The model's target-label mapping is unavailable for verified feedback.")

    original_path = f"datasets/{source_version.dataset_id}/versions/{source_version.id}/original.csv"
    try:
        original_df = pd.read_csv(io.BytesIO(artifact_storage.load(original_path)))
    except Exception as exc:
        raise HTTPException(status_code=404, detail="The original dataset artifact is unavailable.") from exc
    if target_column not in original_df.columns:
        raise HTTPException(status_code=422, detail="The model target column is missing from its source dataset.")

    feedback_rows = []
    for item in feedbacks:
        values = dict(item.original_input or {})
        if not set(selected_features).issubset(values):
            raise HTTPException(status_code=422, detail=f"Feedback for prediction {item.prediction_id} is missing required model features.")
        values[target_column] = inverse_target_mapping[int(item.verified_label)]
        feedback_rows.append(values)
    combined_df = pd.concat([original_df, pd.DataFrame(feedback_rows)], ignore_index=True)

    retrain_tag = f"{source_version.version_tag}-feedback-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    new_version = DatasetVersion(
        dataset_id=str(source_version.dataset_id),
        user_id=str(current_user.id),
        version_tag=retrain_tag,
        row_count=len(combined_df),
        column_count=len(combined_df.columns),
        status="uploaded",
        dataset_metadata={
            **(source_version.dataset_metadata or {}),
            "filename": retrain_tag + ".csv",
            "format": "csv",
            "retrained_from_version_id": str(source_version.id),
            "verified_feedback_count": len(feedback_rows),
            "processing_status": {"uploaded": True, "preprocessed": False, "feature_selection": False},
        },
    )
    await new_version.insert()
    new_version_path = f"datasets/{source_version.dataset_id}/versions/{new_version.id}/original.csv"
    self_csv = combined_df.to_csv(index=False).encode("utf-8")
    artifact_storage.save(new_version_path, self_csv)
    new_version.dataset_metadata["file_size_bytes"] = len(self_csv)
    await new_version.save()

    source_feature_run = await FeatureSelectionRun.get(PydanticObjectId(source_feature_run_id)) if source_feature_run_id else None
    if not source_feature_run or source_feature_run.user_id != str(current_user.id):
        raise HTTPException(status_code=404, detail="The model's original feature-selection run is unavailable.")
    cloned_feature_run = FeatureSelectionRun(
        dataset_version_id=str(new_version.id), user_id=str(current_user.id), target_column=target_column,
        ranking_method=source_feature_run.ranking_method, feature_count=len(selected_features),
        selected_features=selected_features, ranking_scores=source_feature_run.ranking_scores,
        status="completed",
    )
    await cloned_feature_run.insert()

    source_preprocessing = await PreprocessingRun.get(PydanticObjectId(source_preprocessing_id)) if source_preprocessing_id else None
    saved_steps = (source_preprocessing.config_params or {}).get("steps", []) if source_preprocessing else []
    plan = PreprocessingPlan(
        dataset_id=str(source_version.dataset_id), dataset_version_id=str(new_version.id),
        target_column=target_column,
        steps=[PreprocessingPlanStep.model_validate(step) for step in saved_steps] if saved_steps else TrainingService._default_plan_steps(combined_df, selected_features),
        summary="Versioned retraining pipeline using the parent model's approved preprocessing steps.",
    )
    from app.agents.preprocessing_agent.interface import PreprocessingAgent
    import numpy as np
    import sklearn

    processed = PreprocessingAgent().execute_plan(combined_df, plan, target_column, feature_columns=selected_features)
    new_preprocessing = PreprocessingRun(
        dataset_version_id=str(new_version.id), user_id=str(current_user.id), status="completed",
        config_params={"mode": "feedback_retraining", "target_column": target_column,
                       "steps": [step.model_dump(mode="json") for step in plan.steps],
                       "plan_generation_method": "inherited", "source_preprocessing_run_id": str(source_preprocessing.id) if source_preprocessing else None},
    )
    await new_preprocessing.insert()
    processed_path = f"datasets/{source_version.dataset_id}/versions/{new_version.id}/artifacts/preprocessing_{new_preprocessing.id}.joblib"
    processed_buffer = io.BytesIO()
    joblib.dump(processed, processed_buffer)
    artifact_storage.save(processed_path, processed_buffer.getvalue())
    preprocessing_artifact = PreprocessingArtifact(
        dataset_id=str(source_version.dataset_id), dataset_version_id=str(new_version.id),
        preprocessing_run_id=str(new_preprocessing.id), user_id=str(current_user.id),
        pipeline_config={"steps": [step.model_dump(mode="json") for step in plan.steps], "generation_method": "inherited"},
        original_features=processed["original_features"], selected_features=selected_features,
        final_features=processed["feature_names"], target_column=target_column,
        train_split_metadata={"samples": processed["train_samples"]},
        validation_split_metadata={"samples": processed["val_samples"]},
        test_split_metadata={"samples": processed["test_samples"]},
        feature_schema={name: "float64" for name in processed["feature_names"]},
        final_feature_count=len(processed["feature_names"]), output_dataset_location="artifact storage",
        artifact_storage_path=processed_path,
        library_versions={"sklearn": sklearn.__version__, "pandas": pd.__version__, "numpy": np.__version__},
    )
    await preprocessing_artifact.insert()
    new_preprocessing.artifact_storage_path = processed_path
    new_preprocessing.is_ready_for_training = True
    new_preprocessing.target_column = target_column
    new_preprocessing.final_feature_names = processed["feature_names"]
    new_preprocessing.final_feature_count = len(processed["feature_names"])
    await new_preprocessing.save()

    new_version.status = "feature_selected"
    new_version.dataset_metadata["processing_status"] = {"uploaded": True, "preprocessed": True, "feature_selection": True}
    new_version.dataset_metadata["latest_preprocessing_run_id"] = str(new_preprocessing.id)
    new_version.dataset_metadata["latest_feature_selection_run_id"] = str(cloned_feature_run.id)
    new_version.dataset_metadata["selected_features"] = selected_features
    new_version.dataset_metadata["selected_feature_count"] = len(selected_features)
    await new_version.save()

    training_service = TrainingService()
    run = await training_service.execute_training_run(
        user_id=str(current_user.id), model_id=str(model.id), dataset_version_id=str(new_version.id),
        feature_selection_run_id=str(cloned_feature_run.id), preprocessing_run_id=str(new_preprocessing.id),
        hyperparameters=dict(config.get("hyperparameters") or {}),
        is_noisy_quantum=bool((config.get("quantum_config") or {}).get("is_noisy")),
        noise_params=(config.get("hyperparameters") or {}).get("noise_params"),
        custom_name=f"{model.name} · candidate",
    )
    candidate = await Model.get(PydanticObjectId(run.model_id))
    if candidate:
        candidate.status = "candidate"
        candidate.configuration["parent_model_id"] = str(model.id)
        candidate.configuration["model_version"] = int(config.get("model_version", 1)) + 1
        candidate.configuration["candidate_validation_status"] = "awaiting review"
        candidate.configuration["verified_feedback_count"] = len(feedback_rows)
        await candidate.save()

    for item in feedbacks:
        item.status = "used_for_retraining"
        item.used_in_training_run_id = str(run.id)
        await item.save()
    return StandardResponse(
        data=TrainingRunResponse.model_validate(run),
        message="Retraining candidate created from the original dataset plus verified feedback. The parent model remains unchanged; review the candidate's held-out evaluation before using it.",
    )
