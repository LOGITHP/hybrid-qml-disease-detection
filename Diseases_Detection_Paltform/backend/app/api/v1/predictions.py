"""Prediction inference and disease risk stratification endpoints."""

from datetime import datetime, timezone
import io
import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
import joblib
import numpy as np
import pandas as pd
from app.core.dependencies import get_current_user, get_dataset_service
from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.database.models.user import User
from app.database.models.training import TrainingRun
from app.database.models.dataset import Dataset, DatasetVersion
from app.database.models.preprocessing import PreprocessingRun
from app.schemas.prediction import (
    PredictionRequest,
    SinglePredictionResult,
    DatasetOption,
    TrainedModelOption,
    FeatureSchema,
    PredictionSchemaResponse,
    RecommendModelRequest,
    ModelRecommendation,
    RiskStratification,
)
from app.services.artifact_service import artifact_storage
from app.services.dataset_service import DatasetService

router = APIRouter(prefix="/predictions", tags=["Inference & Risk Stratification"])


@router.get("/datasets", response_model=List[DatasetOption])
async def get_prediction_datasets(current_user: User = Depends(get_current_user)):
    """Return datasets that have usable trained models."""
    runs = await TrainingRun.find(
        TrainingRun.user_id == str(current_user.id),
        TrainingRun.status == "completed"
    ).to_list()
    
    dataset_ids = list({run.dataset_version_id for run in runs})
    versions = await DatasetVersion.find({"_id": {"$in": [uuid.UUID(vid) if '-' in vid else vid for vid in dataset_ids]}}).to_list()
    
    unique_ds_ids = list({v.dataset_id for v in versions})
    datasets = await Dataset.find({"_id": {"$in": unique_ds_ids}}).to_list()
    
    return [DatasetOption(dataset_id=str(d.id), name=d.name) for d in datasets]


@router.get("/models", response_model=List[TrainedModelOption])
async def get_compatible_models(dataset_id: str, current_user: User = Depends(get_current_user)):
    """Return compatible completed TrainingRuns for a dataset."""
    versions = await DatasetVersion.find(DatasetVersion.dataset_id == uuid.UUID(dataset_id)).to_list()
    version_ids = [str(v.id) for v in versions]
    
    runs = await TrainingRun.find(
        TrainingRun.user_id == str(current_user.id),
        TrainingRun.status == "completed",
        {"dataset_version_id": {"$in": version_ids}}
    ).to_list()
    
    return [
        TrainedModelOption(
            training_run_id=str(run.id),
            model_type=run.model_type,
            preprocessing_run_id=run.preprocessing_artifact_id,
            metrics=run.metrics or {},
            features_count=len(run.feature_config.get("selected_features", []))
        )
        for run in runs
    ]


@router.post("/recommend-model", response_model=ModelRecommendation)
async def recommend_model(payload: RecommendModelRequest, current_user: User = Depends(get_current_user)):
    """Return the configured recommended model and the metrics supporting the recommendation."""
    versions = await DatasetVersion.find(DatasetVersion.dataset_id == uuid.UUID(payload.dataset_id)).to_list()
    version_ids = [str(v.id) for v in versions]
    
    runs = await TrainingRun.find(
        TrainingRun.user_id == str(current_user.id),
        TrainingRun.status == "completed",
        {"dataset_version_id": {"$in": version_ids}}
    ).to_list()
    
    if not runs:
        raise HTTPException(status_code=404, detail="No trained models available for this dataset.")
        
    # Configuration weights for prototype early-detection priority
    weights = {
        "sensitivity": 0.30,
        "specificity": 0.20,
        "f1_score": 0.20,
        "balanced_accuracy": 0.15,
        "roc_auc": 0.15
    }
    
    best_run = None
    best_score = -1.0
    
    for run in runs:
        m = run.metrics or {}
        score = (
            (m.get("sensitivity", 0) * weights["sensitivity"]) +
            (m.get("specificity", 0) * weights["specificity"]) +
            (m.get("f1_score", 0) * weights["f1_score"]) +
            (m.get("balanced_accuracy", 0) * weights["balanced_accuracy"]) +
            (m.get("roc_auc", 0) or 0) * weights["roc_auc"]
        )
        if score > best_score:
            best_score = score
            best_run = run
            
    if not best_run:
        raise HTTPException(status_code=404, detail="Could not score any models.")
        
    return ModelRecommendation(
        training_run_id=str(best_run.id),
        model_type=best_run.model_type,
        recommendation_score=round(best_score, 4),
        metrics=best_run.metrics or {},
        reason="Highest configured decision-support score among the available trained models for this dataset."
    )


@router.get("/schema", response_model=PredictionSchemaResponse)
async def get_prediction_schema(
    training_run_id: str, 
    current_user: User = Depends(get_current_user),
    dataset_service: DatasetService = Depends(get_dataset_service)
):
    """Return the exact patient input schema required by the selected model."""
    run = await TrainingRun.get(training_run_id)
    if not run or run.user_id != str(current_user.id):
        raise ResourceNotFoundError("TrainingRun", training_run_id)
        
    if not run.preprocessing_artifact_id:
        raise ValidationError("Model unavailable: preprocessing artifact is missing.")
        
    prep_run = await PreprocessingRun.get(run.preprocessing_artifact_id)
    if not prep_run:
        raise ResourceNotFoundError("PreprocessingRun", run.preprocessing_artifact_id)
        
    # Infer types from original dataset columns
    try:
        df = dataset_service.load_version_dataframe(dataset_id=uuid.UUID(prep_run.dataset_version_id), version_id=uuid.UUID(prep_run.dataset_version_id))
    except Exception:
        raise ValidationError("Underlying dataset for schema generation is missing.")
        
    features = run.feature_config.get("selected_features", [])
    
    schema_features = []
    for f in features:
        if f not in df.columns:
            continue
            
        col_series = df[f]
        if pd.api.types.is_numeric_dtype(col_series) and not pd.api.types.is_bool_dtype(col_series):
            unique_vals = col_series.dropna().unique()
            if len(unique_vals) == 2:
                schema_features.append(FeatureSchema(name=f, type="binary", description=f"Binary numerical input (e.g. {unique_vals[0]}, {unique_vals[1]})"))
            else:
                schema_features.append(FeatureSchema(name=f, type="numerical", min_value=float(col_series.min()), max_value=float(col_series.max()), description="Numerical input"))
        else:
            categories = col_series.dropna().astype(str).unique().tolist()
            if len(categories) == 2:
                schema_features.append(FeatureSchema(name=f, type="binary", categories=categories, description="Binary categorical input"))
            else:
                schema_features.append(FeatureSchema(name=f, type="categorical", categories=categories, description="Categorical input"))
                
    return PredictionSchemaResponse(
        training_run_id=training_run_id,
        features=schema_features
    )


@router.post("/predict", response_model=SinglePredictionResult)
async def generate_prediction(
    payload: PredictionRequest,
    current_user: User = Depends(get_current_user),
):
    """Perform real-time model inference using identical training preprocessing."""
    run = await TrainingRun.get(payload.training_run_id)
    if not run or run.user_id != str(current_user.id):
        raise ResourceNotFoundError("TrainingRun", payload.training_run_id)
        
    if not run.preprocessing_artifact_id:
        raise ValidationError("Model unavailable: preprocessing artifact is missing.")
        
    prep_run = await PreprocessingRun.get(run.preprocessing_artifact_id)
    if not prep_run:
        raise ResourceNotFoundError("PreprocessingRun", run.preprocessing_artifact_id)
        
    # 3. Load Preprocessing Artifact
    artifact_rel_path = prep_run.artifact_storage_path
    if not artifact_storage.exists(artifact_rel_path):
        raise ResourceNotFoundError("PreprocessingArtifact", artifact_rel_path)
        
    artifact_bytes = artifact_storage.load(artifact_rel_path)
    bundle = joblib.load(io.BytesIO(artifact_bytes))
    
    preprocessor = bundle.get("fitted_pipeline", {}).get("preprocessor")
    if not preprocessor:
        raise ValidationError("Preprocessing artifact does not contain a fitted preprocessor.")
        
    # 4. Validate patient input & Feature Ordering
    selected_features = run.feature_config.get("selected_features", [])
    raw_features = {}
    for feature in selected_features:
        raw_features[feature] = payload.patient_data.get(feature)
        
    # 5. Apply identical fitted preprocessing
    raw_frame = pd.DataFrame([raw_features]).replace({None: np.nan})
    try:
        x_model = preprocessor.transform(raw_frame)
    except Exception as e:
        raise ValidationError(f"Preprocessing transform failed: {str(e)}")
        
    # 6. Load Trained Model
    model_artifact_path = f"models/{run.id}/model.joblib"
    if not artifact_storage.exists(model_artifact_path):
        # Maybe the CML model was saved earlier in models/{model_id}/model.joblib? But we don't use model_id anymore.
        # Check if we have the model saved under training_run_id
        raise ResourceNotFoundError("TrainedModelArtifact", model_artifact_path)
        
    model_bytes = artifact_storage.load(model_artifact_path)
    model_bundle = joblib.load(io.BytesIO(model_bytes))
    model = model_bundle["model"]
    
    # 7. Generate Prediction
    # Assuming VQC or SVM supports predict_proba
    proba = float(model.predict_proba(x_model)[0])
    
    # 8. Generate Score & Apply threshold
    threshold = payload.threshold if payload.threshold is not None else 0.5
    pred_class = int(proba >= threshold)
    pred_label = "POSITIVE" if pred_class == 1 else "NEGATIVE"
    
    # 9. Risk Stratification
    if proba < 0.35:
        risk_level = "LOW"
    elif proba < 0.65:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"
        
    explanation = None
    if run.model_type == "SVM" and hasattr(model, "coef_"):
        # simple linear SVM explainability
        contribs = (model.coef_[0] * x_model[0]).tolist()
        feat_names = bundle.get("feature_names", selected_features)
        explanation = {"top_features": [{"feature": f, "contribution": c} for f, c in zip(feat_names, contribs)]}
    elif run.model_type == "VQC":
        # simple VQC explainability placeholder based on weights
        feat_names = bundle.get("feature_names", selected_features)
        explanation = {"top_features": [{"feature": f, "contribution": 0.0} for f in feat_names]}

    return SinglePredictionResult(
        training_run_id=str(run.id),
        dataset_id=run.dataset_version_id,
        model_type=run.model_type,
        score=round(proba, 4),
        threshold=threshold,
        prediction=pred_class,
        predicted_label=pred_label,
        risk_category=risk_level,
        explanation=explanation
    )
