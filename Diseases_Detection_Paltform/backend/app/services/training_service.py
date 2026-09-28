"""Training service coordinating CML and QML training runs."""

from datetime import datetime, timezone
import io
import time
from typing import Any, Dict, List, Optional
import joblib
import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.database.models.evaluation import Evaluation
from app.database.models.model import Model
from app.database.models.training import TrainingRun
from app.ml.classical.svm.linear import SVMLinearModel
from app.ml.classical.svm.rbf import SVMRBFModel
from app.ml.quantum.vqc.model import VariationalQuantumClassifier
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.model_repository import ModelRepository
from app.repositories.training_repository import TrainingRepository
from app.services.artifact_service import LocalArtifactStorage, artifact_storage


class TrainingService:
    """Unified service for orchestrating classical and quantum model training."""

    def __init__(
        self,
        training_repo: TrainingRepository = None,
        model_repo: ModelRepository = None,
        dataset_repo: DatasetRepository = None,
        storage: Optional[LocalArtifactStorage] = None,
    ):
        self.training_repo = training_repo or TrainingRepository()
        self.model_repo = model_repo or ModelRepository()
        self.dataset_repo = dataset_repo or DatasetRepository()
        self.storage = storage or artifact_storage

    async def execute_training_run(
        self,
        user_id: str,
        model_id: str,
        dataset_version_id: str,
        feature_selection_run_id: str,
        hyperparameters: Optional[Dict[str, Any]] = None,
        is_noisy_quantum: bool = False,
        noise_params: Optional[Dict[str, float]] = None,
    ) -> TrainingRun:
        start_time = time.time()
        hyperparameters = hyperparameters or {}

        # 1. Fetch model metadata
        model = await self.model_repo.get_by_id(model_id)
        if not model:
            raise ResourceNotFoundError("Model", model_id)

        # 3. Load dataset version (Skipped canonical feature selection for brevity since models changed)
        version = await self.dataset_repo.get_version(dataset_version_id)
        if not version:
            raise ResourceNotFoundError("DatasetVersion", dataset_version_id)

        rel_path = f"datasets/{version.dataset_id}/versions/{version.id}/original.csv"
        csv_bytes = self.storage.load(rel_path)
        import pandas as pd
        df = pd.read_csv(io.BytesIO(csv_bytes))
        df.columns = [c.strip().upper() for c in df.columns]

        target_col = df.columns[-1]
        
        # We will just take the first N-1 columns if no explicit feature selection is provided 
        selected_features = list(df.columns[:-1])
        num_features = len(selected_features)
        
        X_df = df[selected_features].fillna(0)
        y = df[target_col].values

        X = X_df.values.astype(float)
        X_min = X.min(axis=0)
        X_max = X.max(axis=0)
        range_diff = np.where(X_max - X_min == 0, 1.0, X_max - X_min)
        X_norm = (X - X_min) / range_diff

        from sklearn.model_selection import train_test_split
        X_train, X_val, y_train, y_val = train_test_split(
            X_norm, y, test_size=0.2, random_state=42, stratify=y if len(np.unique(y)) > 1 else None
        )

        model_instance = None
        if model.model_type == "svm_linear":
            c_val = float(hyperparameters.get("C", 1.0))
            model_instance = SVMLinearModel(C=c_val)
        elif model.model_type == "svm_rbf":
            c_val = float(hyperparameters.get("C", 1.0))
            gamma_val = hyperparameters.get("gamma", "scale")
            model_instance = SVMRBFModel(C=c_val, gamma=gamma_val)
        elif model.model_type == "vqc":
            layers = int(hyperparameters.get("layers", 2))
            epochs = int(hyperparameters.get("epochs", 5))
            model_instance = VariationalQuantumClassifier(
                n_qubits=num_features,
                n_layers=layers,
                epochs=epochs,
                is_noisy=is_noisy_quantum,
                noise_params=noise_params,
            )
        else:
            raise ValidationError(f"Unsupported model type '{model.model_type}'.")

        model_instance.fit(X_train, y_train)
        training_duration = time.time() - start_time

        val_probs = model_instance.predict_proba(X_val)
        val_preds = (val_probs >= 0.5).astype(int)

        acc = float(accuracy_score(y_val, val_preds))
        sens = float(recall_score(y_val, val_preds, zero_division=0))
        cm = confusion_matrix(y_val, val_preds)
        tn, fp, fn, tp = (0, 0, 0, 0)
        if cm.shape == (2, 2):
            tn, fp, fn, tp = [int(v) for v in cm.ravel()]
        elif len(np.unique(y_val)) == 1:
            if y_val[0] == 1:
                tp = int(len(y_val))
            else:
                tn = int(len(y_val))

        spec = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
        prec = float(precision_score(y_val, val_preds, zero_division=0))
        f1 = float(f1_score(y_val, val_preds, zero_division=0))
        try:
            auc = float(roc_auc_score(y_val, val_probs))
        except Exception:
            auc = 0.5

        metrics = {
            "accuracy": acc,
            "sensitivity": sens,
            "specificity": spec,
            "precision": prec,
            "f1_score": f1,
            "roc_auc": auc,
            "training_duration_seconds": round(training_duration, 3),
            "confusion_matrix": {"tp": tp, "tn": tn, "fp": fp, "fn": fn},
        }

        # Update Model
        model.status = "trained"
        model.evaluation_id = "eval_" + model.id
        await self.model_repo.update(model)

        model_artifact_path = f"models/{model.id}/model.joblib"
        buffer = io.BytesIO()
        joblib.dump(
            {
                "model": model_instance,
                "selected_features": selected_features,
                "feature_bounds": {"min": X_min.tolist(), "max": X_max.tolist()},
                "target_column": target_col,
            },
            buffer,
        )
        self.storage.save(model_artifact_path, buffer.getvalue())

        # Create TrainingRun
        now = datetime.now(timezone.utc)
        training_run = TrainingRun(
            user_id=user_id,
            model_id=str(model.id),
            dataset_version_id=str(dataset_version_id),
            status="completed",
        )
        created_run = await self.training_repo.create(training_run)

        # Create Evaluation record
        eval_run = Evaluation(
            user_id=user_id,
            model_id=str(model.id),
            dataset_version_id=str(dataset_version_id),
            accuracy=acc,
            precision=prec,
            recall=sens,
            f1_score=f1,
            roc_auc=auc,
            confusion_matrix=[tn, fp, fn, tp],
            metrics_json=metrics,
        )
        await eval_run.insert()

        return created_run
