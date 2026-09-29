"""Inference using each trained model's saved preprocessing and feature order."""

from datetime import datetime, timezone
import io
from typing import List

import joblib
import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user, get_model_service
from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.database.models.user import User
from app.schemas.prediction import PredictionRequest, PredictionResponse, RiskStratification, SinglePredictionResult
from app.services.artifact_service import artifact_storage
from app.services.model_service import ModelService

router = APIRouter(prefix="/predictions", tags=["Inference & Risk Stratification"])


@router.post("", response_model=PredictionResponse)
async def generate_prediction(
    payload: PredictionRequest,
    current_user: User = Depends(get_current_user),
    model_service: ModelService = Depends(get_model_service),
):
    """Apply the selected trained model to one or more schema-matched input rows."""
    model_obj = await model_service.get_model(
        model_id=payload.model_id,
        user_id=str(current_user.id),
        is_admin=(current_user.role == "admin"),
    )
    if model_obj.status != "trained":
        raise ValidationError("Choose a model that has been trained on an uploaded dataset.")

    artifact_path = f"models/{model_obj.id}/model.joblib"
    if not artifact_storage.exists(artifact_path):
        raise ResourceNotFoundError("TrainedModelArtifact", artifact_path)
    bundle = joblib.load(io.BytesIO(artifact_storage.load(artifact_path)))
    model = bundle.get("model")
    selected_features = bundle.get("selected_features") or []
    preprocessor = bundle.get("preprocessor")
    if model is None or not selected_features or preprocessor is None:
        raise ValidationError("The trained model artifact is missing its estimator, selected features, or fitted preprocessor.")

    raw_items = payload.features if isinstance(payload.features, list) else [payload.features]
    if not raw_items:
        raise ValidationError("Provide at least one input row for prediction.")
    threshold = payload.decision_threshold if payload.decision_threshold is not None else 0.5
    results: List[SinglePredictionResult] = []
    for index, item in enumerate(raw_items):
        unexpected_features = sorted(set(item) - set(selected_features))
        if unexpected_features:
            raise ValidationError(
                f"Input contains columns this model was not trained to use: {', '.join(unexpected_features)}."
            )
        raw_features = {feature: item.get(feature) for feature in selected_features}
        raw_frame = pd.DataFrame([raw_features]).replace({None: np.nan})
        try:
            x_model = preprocessor.transform(raw_frame)
            order_indices = bundle.get("preprocessor_feature_order_indices")
            if order_indices is not None:
                x_model = x_model[:, order_indices]
            probability = float(_positive_class_probabilities(model, x_model)[0])
        except Exception as exc:
            raise ValidationError(f"Input values could not be transformed by this model's saved preprocessing: {exc}") from exc

        predicted_class = int(probability >= threshold)
        if probability < 0.35:
            risk_level = "LOW"
        elif probability < 0.65:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
        results.append(SinglePredictionResult(
            predicted_class=predicted_class,
            predicted_label="POSITIVE" if predicted_class else "NEGATIVE",
            probability=round(probability, 4),
            risk_stratification=RiskStratification(risk_level=risk_level, score=round(probability, 4)),
            input_features_used=selected_features,
            sample_id=f"sample-{index + 1}",
        ))

    return PredictionResponse(
        model_id=str(model_obj.id),
        preprocessing_run_id=bundle.get("preprocessing_run_id"),
        feature_selection_run_id=bundle.get("feature_selection_run_id"),
        decision_threshold_applied=threshold,
        results=results,
        timestamp=datetime.now(timezone.utc),
    )


def _positive_class_probabilities(model, values):
    """Accept project wrappers and raw pretrained scikit-learn estimators."""
    probabilities = np.asarray(model.predict_proba(values), dtype=float)
    if probabilities.ndim == 1:
        return probabilities
    classes = np.asarray(getattr(model, "classes_", np.arange(probabilities.shape[1])))
    positive_indices = np.flatnonzero(classes == 1)
    positive_index = int(positive_indices[0]) if positive_indices.size else probabilities.shape[1] - 1
    return probabilities[:, positive_index]
