"""Prediction inference and disease risk stratification endpoints."""

from datetime import datetime, timezone
import io
from typing import List
from fastapi import APIRouter, Depends
import joblib
import numpy as np
import pandas as pd
from app.core.dependencies import get_current_user, get_model_service
from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.database.models.user import User
from app.schemas.prediction import (
    PredictionRequest,
    PredictionResponse,
    RiskStratification,
    SinglePredictionResult,
)
from app.services.artifact_service import artifact_storage
from app.services.model_service import ModelService

router = APIRouter(prefix="/predictions", tags=["Inference & Risk Stratification"])


@router.post("", response_model=PredictionResponse)
async def generate_prediction(
    payload: PredictionRequest,
    current_user: User = Depends(get_current_user),
    model_service: ModelService = Depends(get_model_service),
):
    """Perform real-time model inference with configurable decision threshold and clinical risk stratification."""
    model_obj = await model_service.get_model(
        model_id=payload.model_id,
        user_id=str(current_user.id),
        is_admin=(current_user.role == "admin"),
    )

    artifact_rel_path = f"models/{model_obj.id}/model.joblib"
    if not artifact_storage.exists(artifact_rel_path):
        raise ResourceNotFoundError("TrainedModelArtifact", artifact_rel_path)

    artifact_bytes = artifact_storage.load(artifact_rel_path)
    bundle = joblib.load(io.BytesIO(artifact_bytes))

    model = bundle["model"]
    selected_features = bundle["selected_features"]
    preprocessor = bundle.get("preprocessor")
    feature_bounds = bundle.get("feature_bounds")

    raw_items = payload.features if isinstance(payload.features, list) else [payload.features]
    results: List[SinglePredictionResult] = []
    threshold = payload.decision_threshold if payload.decision_threshold is not None else 0.5

    for idx, item in enumerate(raw_items):
        # Reuse the exact preprocessing pipeline fitted on the selected training split.
        raw_features = {feature: item.get(feature) for feature in selected_features}
        if preprocessor is not None:
            raw_frame = pd.DataFrame([raw_features]).replace({None: np.nan})
            x_model = preprocessor.transform(raw_frame)
        elif feature_bounds is not None:
            # Backward compatibility for model artifacts saved before schema-aware preprocessing.
            x_raw = np.asarray([float(raw_features.get(feature) or 0.0) for feature in selected_features])
            min_vals = np.asarray(feature_bounds["min"])
            max_vals = np.asarray(feature_bounds["max"])
            range_diff = np.where(max_vals - min_vals == 0, 1.0, max_vals - min_vals)
            x_model = np.clip((x_raw - min_vals) / range_diff, 0.0, 1.0).reshape(1, -1)
        else:
            raise ResourceNotFoundError("ModelPreprocessor", artifact_rel_path)

        # Compute probability
        proba = float(model.predict_proba(x_model)[0])
        pred_class = int(proba >= threshold)
        pred_label = "POSITIVE" if pred_class == 1 else "NEGATIVE"

        # Stratify risk level
        if proba < 0.35:
            risk_level = "LOW"
        elif proba < 0.65:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"

        risk_strat = RiskStratification(
            risk_level=risk_level,
            score=round(proba, 4),
        )

        results.append(
            SinglePredictionResult(
                predicted_class=pred_class,
                predicted_label=pred_label,
                probability=round(proba, 4),
                risk_stratification=risk_strat,
                input_features_used=selected_features,
                sample_id=f"sample-{idx+1}",
            )
        )

    return PredictionResponse(
        model_id=str(model_obj.id),
        preprocessing_run_id=bundle.get("preprocessing_run_id"),
        feature_selection_run_id=bundle.get("feature_selection_run_id"),
        decision_threshold_applied=threshold,
        results=results,
        timestamp=datetime.now(timezone.utc),
    )
