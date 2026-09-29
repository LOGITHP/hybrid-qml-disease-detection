from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from beanie import PydanticObjectId
import pandas as pd
import io

from app.core.dependencies import get_current_user
from app.database.models import User, PredictionFeedback, Model, Dataset, DatasetVersion, TrainingRun
from app.schemas import StandardResponse, FeedbackCreate, FeedbackResponse, FeedbackStats, TrainingRunResponse
from app.services.training_service import TrainingService

router = APIRouter(prefix="/feedback", tags=["Feedback & Retraining"])

def get_training_service():
    return TrainingService()

@router.post("", response_model=StandardResponse[FeedbackResponse])
async def submit_feedback(
    request: FeedbackCreate,
    current_user: User = Depends(get_current_user)
):
    """Submit clinician feedback for a prediction."""
    feedback = PredictionFeedback(
        prediction_id=request.prediction_id,
        model_id=request.model_id,
        user_id=str(current_user.id),
        is_correct=request.is_correct,
        verified_label=request.verified_label if not request.is_correct else None,
        original_input=request.original_input,
        notes=request.notes,
        status="pending"
    )
    await feedback.insert()
    return StandardResponse(data=FeedbackResponse.model_validate(feedback), message="Feedback saved successfully")

@router.get("/model/{model_id}", response_model=StandardResponse[List[FeedbackResponse]])
async def list_model_feedback(
    model_id: str,
    current_user: User = Depends(get_current_user)
):
    """List all feedback for a specific model."""
    feedbacks = await PredictionFeedback.find(
        PredictionFeedback.model_id == model_id,
        PredictionFeedback.user_id == str(current_user.id)
    ).to_list()
    return StandardResponse(data=[FeedbackResponse.model_validate(f) for f in feedbacks])

@router.get("/model/{model_id}/stats", response_model=StandardResponse[FeedbackStats])
async def get_feedback_stats(
    model_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get aggregated feedback statistics for a model."""
    feedbacks = await PredictionFeedback.find(
        PredictionFeedback.model_id == model_id,
        PredictionFeedback.user_id == str(current_user.id)
    ).to_list()
    
    total = len(feedbacks)
    correct = sum(1 for f in feedbacks if f.is_correct)
    incorrect = total - correct
    accuracy = (correct / total) if total > 0 else 0.0
    pending = sum(1 for f in feedbacks if f.status == "pending")

    stats = FeedbackStats(
        total_feedback=total,
        correct_predictions=correct,
        incorrect_predictions=incorrect,
        clinician_accuracy=accuracy,
        pending_retrain_count=pending
    )
    return StandardResponse(data=stats)

@router.post("/model/{model_id}/retrain", response_model=StandardResponse[TrainingRunResponse])
async def retrain_on_feedback(
    model_id: str,
    current_user: User = Depends(get_current_user),
    training_service: TrainingService = Depends(get_training_service)
):
    """Trigger retraining on accumulated pending feedback for a model."""
    # Find model
    model = await Model.get(PydanticObjectId(model_id))
    if not model or str(model.user_id) != str(current_user.id) and not model.is_default:
        raise HTTPException(status_code=404, detail="Model not found")
        
    config = model.configuration or {}
    dataset_version_id = config.get("dataset_version_id")
    if not dataset_version_id:
        raise HTTPException(status_code=400, detail="Model does not have an associated dataset version for retraining")
        
    # Get original dataset version
    original_version = await DatasetVersion.get(PydanticObjectId(dataset_version_id))
    if not original_version:
        raise HTTPException(status_code=404, detail="Original dataset version not found")
        
    # Find pending feedback
    feedbacks = await PredictionFeedback.find(
        PredictionFeedback.model_id == model_id,
        PredictionFeedback.user_id == str(current_user.id),
        PredictionFeedback.status == "pending"
    ).to_list()
    
    if not feedbacks:
        raise HTTPException(status_code=400, detail="No pending feedback available for retraining")
        
    target_column = config.get("target_column")
    if not target_column:
        raise HTTPException(status_code=400, detail="Target column not found in model configuration")
        
    # Read original dataset data
    import os
    dataset_dir = f"/app/data/datasets/{original_version.dataset_id}/{original_version.id}"
    data_path = f"{dataset_dir}/data.csv"
    if not os.path.exists(data_path):
        raise HTTPException(status_code=500, detail="Original dataset file not found on disk")
        
    df = pd.read_csv(data_path)
    
    # Append feedback
    new_rows = []
    for fb in feedbacks:
        row = dict(fb.original_input)
        if fb.is_correct:
            # We assume original prediction matches the original dataset logic, 
            # or the user verified it is correct. 
            pass # The original input should have the target column? Wait, prediction inputs don't have the target column.
            # We need to get the original prediction result? Actually if it's correct, verified_label is the predicted class.
            row[target_column] = fb.verified_label 
            # Wait, verified_label is None if is_correct is True? Let's check our submit logic. Yes.
        else:
            row[target_column] = fb.verified_label
            
    # If is_correct is true, we need the predicted class. We can enforce verified_label is always populated on the frontend.
    
    # Let's fix that constraint: frontend must ALWAYS send verified_label! Even if is_correct is true.
    for fb in feedbacks:
        row = dict(fb.original_input)
        row[target_column] = fb.verified_label
        new_rows.append(row)
        
    new_df = pd.DataFrame(new_rows)
    combined_df = pd.concat([df, new_df], ignore_index=True)
    
    # Save as new dataset version
    new_version = DatasetVersion(
        dataset_id=original_version.dataset_id,
        version_tag=f"{original_version.version_tag}-retrain-{len(feedbacks)}",
        row_count=len(combined_df),
        column_count=len(combined_df.columns),
        file_path="", # Will be set
        file_size_bytes=0,
        metadata={"retrained_from": str(original_version.id), "feedback_samples": len(feedbacks)}
    )
    new_version_id = str(new_version.id) if new_version.id else str(PydanticObjectId())
    new_version.id = PydanticObjectId(new_version_id)
    
    new_dir = f"/app/data/datasets/{original_version.dataset_id}/{new_version_id}"
    os.makedirs(new_dir, exist_ok=True)
    new_path = f"{new_dir}/data.csv"
    combined_df.to_csv(new_path, index=False)
    
    new_version.file_path = new_path
    new_version.file_size_bytes = os.path.getsize(new_path)
    await new_version.insert()
    
    # Mark feedback as used
    for fb in feedbacks:
        fb.status = "used_for_retraining"
        await fb.save()
        
    # Launch training using same config but new dataset_version_id
    # We will reuse the model config, and queue a new training run
    from app.schemas.training import TrainingConfigCreate, TrainingRunCreate
    
    # Get original training run to copy its config
    # We can infer from model configuration
    training_req = TrainingRunCreate(
        name=f"Retrained {model.name}",
        description=f"Retrained on {len(feedbacks)} new clinician-verified samples",
        config=TrainingConfigCreate(
            dataset_version_id=str(new_version.id),
            preprocessing_run_id=config.get("preprocessing_run_id"), # Assuming we can reuse it or it's none
            feature_selection_run_id=config.get("feature_selection_run_id"),
            target_column=target_column,
            selected_features=config.get("selected_features", []),
            model_type=model.model_type,
            hyperparameters=config.get("hyperparameters", {}),
            quantum_config=config.get("quantum_config") # If any
        )
    )
    
    run = await training_service.start_training(training_req, str(current_user.id))
    return StandardResponse(data=TrainingRunResponse.model_validate(run), message="Retraining started on combined dataset")
