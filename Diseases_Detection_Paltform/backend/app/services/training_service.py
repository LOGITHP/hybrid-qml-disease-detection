"""Dataset-driven training for the platform's built-in model templates."""

import io
import time
from typing import Any, Dict, Optional

import joblib
import numpy as np
import logging
import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score

from app.agents.preprocessing_agent.interface import PreprocessingAgent
from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.database.models.evaluation import Evaluation
from app.database.models.experiment import Experiment
from app.database.models.feature_selection import FeatureSelectionRun
from app.database.models.model import Model
from app.database.models.preprocessing import PreprocessingArtifact, PreprocessingRun
from app.database.models.training import TrainingRun
from app.ml.classical.svm.linear import SVMLinearModel
from app.ml.classical.svm.rbf import SVMRBFModel
from app.ml.loader import pretrained_model_loader
from app.ml.quantum.vqc.model import VariationalQuantumClassifier
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.model_repository import ModelRepository
from app.repositories.training_repository import TrainingRepository
from app.schemas.preprocessing import PreprocessingPlan, PreprocessingPlanStep
from app.services.artifact_service import LocalArtifactStorage, artifact_storage


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TrainingService:
    """Train a selected template against an uploaded dataset and its saved pipeline."""

    def __init__(self, training_repo=None, model_repo=None, dataset_repo=None, storage: Optional[LocalArtifactStorage] = None):
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
        preprocessing_run_id: Optional[str] = None,
        hyperparameters: Optional[Dict[str, Any]] = None,
        is_noisy_quantum: bool = False,
        noise_params: Optional[Dict[str, float]] = None,
        custom_name: Optional[str] = None,
    ) -> TrainingRun:
        started_at = time.time()
        logger.debug(f"[TRAINING TRACE] Starting execute_training_run with model_id={model_id}, dataset_version_id={dataset_version_id}")
        hyperparameters = hyperparameters or {}

        template = await self.model_repo.get_by_id(model_id)
        if not template or (template.user_id != user_id and not template.is_default):
            raise ResourceNotFoundError("Model", model_id)
        version = await self.dataset_repo.get_version(dataset_version_id)
        if not version or version.user_id != user_id:
            raise ResourceNotFoundError("DatasetVersion", dataset_version_id)

        feature_run = await FeatureSelectionRun.get(feature_selection_run_id)
        if not feature_run or feature_run.user_id != user_id or str(feature_run.dataset_version_id) != str(dataset_version_id):
            raise ResourceNotFoundError("FeatureSelectionRun", feature_selection_run_id)
        features = list(feature_run.selected_features or [])
        target = feature_run.target_column
        if not features:
            raise ValidationError("The feature-selection run does not contain selected feature columns.")

        csv_path = f"datasets/{version.dataset_id}/versions/{version.id}/original.csv"
        logger.debug(f"[TRAINING TRACE] Loading dataset from path: {csv_path}")
        df = pd.read_csv(io.BytesIO(self.storage.load(csv_path)))
        logger.debug(f"[TRAINING TRACE] Loaded dataset. Shape: {df.shape}")
        if not target or target not in df.columns:
            raise ValidationError("Select a valid target column in Feature Selection before training.")
        if df[target].isna().any():
            raise ValidationError(f"Target column '{target}' contains missing values; resolve them before training.")
        invalid = [column for column in features if column not in df.columns or column == target]
        if invalid:
            raise ValidationError(f"Selected feature columns are invalid: {', '.join(invalid)}.")

        preprocessing_run = None
        if preprocessing_run_id:
            preprocessing_run = await PreprocessingRun.get(preprocessing_run_id)
            if not preprocessing_run or preprocessing_run.user_id != user_id or str(preprocessing_run.dataset_version_id) != str(dataset_version_id):
                raise ResourceNotFoundError("PreprocessingRun", preprocessing_run_id)
            if preprocessing_run.status != "completed":
                raise ValidationError("The selected preprocessing run has not completed.")
            config = preprocessing_run.config_params or {}
            configured_target = config.get("target_column")
            if configured_target and configured_target != target:
                raise ValidationError("Preprocessing and feature selection use different target columns.")
            steps_data = config.get("steps") or []
            if not steps_data:
                artifact = await PreprocessingArtifact.find_one({
                    "preprocessing_run_id": str(preprocessing_run.id),
                    "user_id": user_id,
                })
                steps_data = (artifact.pipeline_config or {}).get("steps", []) if artifact else []
            if not steps_data:
                raise ValidationError("The selected preprocessing run has no saved transformation steps. Re-run preprocessing before training.")
            steps = [PreprocessingPlanStep.model_validate(step) for step in steps_data]
        else:
            steps = self._default_plan_steps(df, features)

        plan = PreprocessingPlan(
            dataset_id=str(version.dataset_id), dataset_version_id=str(version.id), steps=steps,
            summary="Saved preprocessing configuration for the selected upload.",
        )
        logger.debug(f"[TRAINING TRACE] Executing preprocessing plan with {len(steps)} steps. Selected features: {features}")
        processed = PreprocessingAgent().execute_plan(df, plan, target, feature_columns=features)
        logger.debug(f"[TRAINING TRACE] Preprocessing complete. X_train.shape={processed['X_train'].shape}, X_test.shape={processed['X_test'].shape}")
        omitted = sorted(set(features) - set(processed["original_features"]))
        if omitted:
            raise ValidationError(
                f"Selected features are omitted by preprocessing: {', '.join(omitted)}. "
                "Encode those categorical columns or remove them from feature selection."
            )

        X_train, X_test = processed["X_train"], processed["X_test"]
        template_config = template.configuration or {}
        is_pretrained = bool(template_config.get("pretrained"))
        layers = int(template_config.get("n_layers", hyperparameters.get("layers", 2)))
        configured_encoding = str(template_config.get("encoding", "")).lower()
        encoding_method = str(hyperparameters.get(
            "encoding_method", "angle_rx" if "rx" in configured_encoding else "angle_ry"
        ))
        variational_gate = str(hyperparameters.get("variational_gate", "RY"))
        entanglement_strategy = str(hyperparameters.get("entanglement_strategy", "linear_cnot"))
        is_noisy_quantum = bool(is_noisy_quantum or template_config.get("noise_channels"))
        noise_params = noise_params or template_config.get("noise_channels")
        if is_pretrained:
            checkpoint_features = template_config.get("selected_features") or []
            if target.strip().lower() != "lung_cancer" or features != checkpoint_features:
                raise ValidationError("This pretrained checkpoint requires target LUNG_CANCER and its exact documented feature order.")
            non_numeric = [
                column for column in features
                if not pd.api.types.is_numeric_dtype(df[column]) or pd.api.types.is_bool_dtype(df[column])
            ]
            if non_numeric or set(processed["original_features"]) != set(features) or len(processed["original_features"]) != len(features):
                raise ValidationError("This pretrained checkpoint requires its documented numeric feature set in the exact selected order.")
            scaler_step = next((step for step in steps if step.tool_name.lower() == "min_max_scaler"), None)
            if not scaler_step or set(scaler_step.parameters.get("columns", [])) != set(features):
                raise ValidationError("This pretrained checkpoint requires min-max scaling on every documented feature.")
            if X_train.shape[1] != int(template_config.get("feature_count", 0)):
                raise ValidationError("The uploaded data's transformed feature count does not match this pretrained checkpoint.")

        classes = sorted({str(value) for value in df[target].dropna().unique()})
        if len(classes) != 2:
            raise ValidationError("The built-in SVM and VQC models require a binary target with exactly two classes.")
        positive_tokens = {"1", "yes", "true", "positive", "case", "disease", "cancer", "present", "affected"}
        positive_class = next((name for name in classes if name.strip().lower() in positive_tokens), classes[-1])
        target_map = {name: int(name == positive_class) for name in classes}
        y_train = np.asarray([target_map[str(value)] for value in processed["y_train"]], dtype=int)
        y_test = np.asarray([target_map[str(value)] for value in processed["y_test"]], dtype=int)
        logger.debug(f"[TRAINING TRACE] Target mapping complete. y_train.shape={y_train.shape}, y_test.shape={y_test.shape}")
        feature_order_indices = []
        for feature in features:
            matched_indices = []
            for i, fname in enumerate(processed["feature_names"]):
                if fname == feature or fname.endswith(f"__{feature}") or f"__{feature}_" in fname:
                    matched_indices.append(i)
            if matched_indices:
                feature_order_indices.extend(matched_indices)
            else:
                # Fallback just in case
                try:
                    feature_order_indices.append(processed["original_features"].index(feature))
                except ValueError:
                    pass

        X_train = X_train[:, feature_order_indices]
        X_test = X_test[:, feature_order_indices]

        logger.debug(f"[TRAINING TRACE] Applied feature selection. X_train.shape={X_train.shape}, X_test.shape={X_test.shape}")

        if is_pretrained and template_config.get("model_file"):
            estimator = pretrained_model_loader.load_classical_svm(template_config["model_file"])
        elif is_pretrained and template_config.get("weights_file") and template_config.get("bias_file"):
            estimator = pretrained_model_loader.load_vqc_model(
                weights_filename=template_config["weights_file"],
                bias_filename=template_config["bias_file"],
                n_qubits=int(template_config.get("n_qubits", template_config.get("feature_count", 0))),
                n_layers=int(template_config.get("n_layers", 2)),
                is_noisy=bool(template_config.get("noise_channels")),
                noise_params=template_config.get("noise_channels"),
            )
        elif template.model_type == "svm_linear":
            c_value = float(hyperparameters.get("C", 1.0))
            if c_value <= 0:
                raise ValidationError("SVM regularization C must be greater than zero.")
            estimator = SVMLinearModel(C=c_value)
        elif template.model_type == "svm_rbf":
            c_value = float(hyperparameters.get("C", 1.0))
            if c_value <= 0:
                raise ValidationError("SVM regularization C must be greater than zero.")
            estimator = SVMRBFModel(C=c_value, gamma=hyperparameters.get("gamma", "scale"))
        elif template.model_type == "vqc":
            layers = int(hyperparameters.get("layers", layers))
            epochs = int(hyperparameters.get("epochs", 5))
            requested_qubits = int(hyperparameters.get("n_qubits", X_train.shape[1]))
            learning_rate = float(hyperparameters.get("learning_rate", 0.03))
            batch_size = int(hyperparameters.get("batch_size", 32))
            encoding_method = str(hyperparameters.get("encoding_method", encoding_method))
            variational_gate = str(hyperparameters.get("variational_gate", variational_gate))
            entanglement_strategy = str(hyperparameters.get("entanglement_strategy", entanglement_strategy))
            backend_type = str(hyperparameters.get("backend_type", "default.qubit"))
            if not 1 <= layers <= 5 or not 1 <= epochs <= 1000:
                raise ValidationError("VQC layers must be 1–5 and epochs must be 1–1000.")
            if encoding_method not in {"angle_ry", "angle_rx"}:
                raise ValidationError("VQC encoding must be angle_ry or angle_rx for this PennyLane circuit implementation.")
            if variational_gate not in {"RY", "RZ"}:
                raise ValidationError("VQC trainable gates must be RY or RZ for this PennyLane circuit implementation.")
            if entanglement_strategy not in {"linear_cnot", "ring_cnot", "none"}:
                raise ValidationError("VQC entanglement must be linear_cnot, ring_cnot, or none.")
            if requested_qubits != X_train.shape[1]:
                raise ValidationError(f"The configured {requested_qubits}-qubit circuit does not match the transformed feature width ({X_train.shape[1]}). Update feature mapping before training.")
            if X_train.shape[1] > 8:
                raise ValidationError("PennyLane simulator runs are limited to 8 encoded feature dimensions; select fewer features or use an SVM baseline.")
            if not 0.0001 <= learning_rate <= 1.0 or not 1 <= batch_size <= 4096:
                raise ValidationError("VQC learning rate must be between 0.0001–1 and batch size must be 1–4096.")
            if is_noisy_quantum:
                noise_params = noise_params or {"p_gate": 0.01, "p_cnot": 0.02, "p_meas": 0.01}
                if any(float(value) < 0 or float(value) > 0.5 for value in noise_params.values()):
                    raise ValidationError("Noisy simulator probabilities must be between 0 and 0.5.")
            estimator = VariationalQuantumClassifier(
                n_qubits=X_train.shape[1], n_layers=layers, epochs=epochs,
                lr=learning_rate, batch_size=batch_size,
                is_noisy=is_noisy_quantum, noise_params=noise_params,
                encoding_method=encoding_method, variational_gate=variational_gate,
                entanglement_strategy=entanglement_strategy,
            )
        else:
            raise ValidationError(f"Unsupported model type '{template.model_type}'.")

        logger.debug(f"[TRAINING TRACE] Model initialization complete for type {template.model_type}. is_pretrained={is_pretrained}")

        if not is_pretrained:
            logger.debug(f"[TRAINING TRACE] Starting estimator fit...")
            estimator.fit(X_train, y_train)
            logger.debug(f"[TRAINING TRACE] Estimator fit completed.")
        duration = time.time() - started_at
        inference_started = time.perf_counter()
        probabilities = _positive_class_probabilities(estimator, X_test)
        inference_duration_ms = round((time.perf_counter() - inference_started) * 1000 / max(len(y_test), 1), 6)
        predictions = (probabilities >= 0.5).astype(int)
        accuracy = float(accuracy_score(y_test, predictions))
        sensitivity = float(recall_score(y_test, predictions, zero_division=0))
        tn, fp, fn, tp = [int(value) for value in confusion_matrix(y_test, predictions, labels=[0, 1]).ravel()]
        specificity = float(tn / (tn + fp)) if tn + fp else 0.0
        precision = float(precision_score(y_test, predictions, zero_division=0))
        f1 = float(f1_score(y_test, predictions, zero_division=0))
        auc = float(roc_auc_score(y_test, probabilities)) if len(np.unique(y_test)) == 2 else None

        # Generalization Metrics (Train)
        train_probs = _positive_class_probabilities(estimator, X_train)
        train_preds = (train_probs >= 0.5).astype(int)
        train_accuracy = float(accuracy_score(y_train, train_preds))
        train_sensitivity = float(recall_score(y_train, train_preds, zero_division=0))
        tr_tn, tr_fp, tr_fn, tr_tp = [int(value) for value in confusion_matrix(y_train, train_preds, labels=[0, 1]).ravel()]
        train_specificity = float(tr_tn / (tr_tn + tr_fp)) if tr_tn + tr_fp else 0.0

        metrics = {
            "accuracy": accuracy, "balanced_accuracy": float(balanced_accuracy_score(y_test, predictions)),
            "sensitivity": sensitivity, "specificity": specificity, "precision": precision,
            "f1_score": f1, "roc_auc": auc, "training_duration_seconds": round(duration, 3),
            "evaluation_partition": "held-out test", "positive_class": positive_class,
            "target_column": target, "selected_features": features,
            "test_samples": int(len(y_test)), "inference_duration_ms": inference_duration_ms,
            "confusion_matrix": {"tp": tp, "tn": tn, "fp": fp, "fn": fn},
            "y_true_test": y_test.tolist(),
            "y_prob_test": probabilities.tolist(),
            "generalization": {
                "train": {
                    "accuracy": train_accuracy,
                    "sensitivity": train_sensitivity,
                    "specificity": train_specificity,
                },
                "test": {
                    "accuracy": accuracy,
                    "sensitivity": sensitivity,
                    "specificity": specificity,
                }
            }
        }

        dataset = await self.dataset_repo.get_by_id(version.dataset_id)
        dataset_name = dataset.name if dataset else "Uploaded dataset"
        trained_model_name = custom_name if custom_name else f"{template.name} · {dataset_name} {version.version_tag}"
        logger.debug(f"[TRAINING TRACE] Creating Model record in database: {trained_model_name}")
        trained_model = await self.model_repo.create(Model(
            user_id=user_id, name=trained_model_name,
            description=(
                f"Pretrained checkpoint evaluated on uploaded dataset version {version.version_tag}."
                if is_pretrained else f"Trained on uploaded dataset version {version.version_tag}."
            ),
            model_type=template.model_type, is_quantum=template.model_type == "vqc",
            is_default=False, status="trained",
            dataset_id=str(version.dataset_id), dataset_version_id=str(version.id),
            preprocessing_run_id=str(preprocessing_run.id) if preprocessing_run else None,
            feature_selection_run_id=str(feature_run.id), selected_features_snapshot=features,
            configuration={
                "dataset_version_id": str(version.id),
                "dataset_version_tag": version.version_tag,
                "dataset_id": str(version.dataset_id),
                "dataset_name": dataset_name,
                "preprocessing_run_id": str(preprocessing_run.id) if preprocessing_run else None,
                "preprocessing_version": 1 if preprocessing_run else None,
                "feature_selection_run_id": str(feature_run.id), "target_column": target,
                "feature_selection_method": feature_run.ranking_method,
                "selected_features": features, "hyperparameters": hyperparameters,
                "training_config": {"random_state": 42, "evaluation_partition": "held-out test"},
                "framework": "PennyLane" if template.model_type == "vqc" else "scikit-learn",
                "model_version": 1,
                "pretrained_used": is_pretrained,
                "pretrained_source_model_id": template_config.get("model_id") if is_pretrained else None,
                "pretrained_source_model_name": template.name if is_pretrained else None,
                "pretrained_source_metrics": template_config.get("metrics") if is_pretrained else None,
                "metrics": {
                    key: metrics.get(key) for key in (
                        "accuracy", "balanced_accuracy", "sensitivity", "specificity", "precision",
                        "f1_score", "roc_auc", "training_duration_seconds", "inference_duration_ms", "test_samples", "confusion_matrix",
                    )
                },
            },
        ))
        trained_model.evaluation_id = f"eval_{trained_model.id}"
        await self.model_repo.update(trained_model)

        buffer = io.BytesIO()
        joblib.dump({
            "model": estimator, "selected_features": features,
            "original_features": processed.get("original_features", []),
            "preprocessor": processed["fitted_pipeline"]["preprocessor"],
            "target_column": target, "target_mapping": target_map, "positive_class": positive_class,
            "encoded_feature_names": processed["feature_names"],
            "preprocessor_feature_order_indices": feature_order_indices,
            "preprocessing_run_id": str(preprocessing_run.id) if preprocessing_run else None,
            "feature_selection_run_id": str(feature_run.id),
        }, buffer)
        logger.debug(f"[TRAINING TRACE] Serializing and saving artifact to models/{trained_model.id}/model.joblib")
        self.storage.save(f"models/{trained_model.id}/model.joblib", buffer.getvalue())

        qml_config = None
        if template.model_type == "vqc":
            import pennylane as qml
            dummy_x = np.zeros(X_train.shape[1])
            dummy_weights = estimator.weights if hasattr(estimator, 'weights') else np.zeros((layers, X_train.shape[1]))
            try:
                specs = qml.specs(estimator.circuit)(dummy_weights, dummy_x)
                qml_config = {
                    "n_qubits": X_train.shape[1],
                    "n_layers": layers,
                    "gates": specs.get("num_operations", 0),
                    "depth": specs.get("depth", 0),
                    "shots": "Analytic (None)",
                    "encoding": "Angle Encoding",
                    "encoding_method": encoding_method,
                    "feature_to_qubit": {name: index for index, name in enumerate(processed["feature_names"])},
                    "variational_gate": variational_gate,
                    "entanglement_strategy": entanglement_strategy,
                    "measurement": "Pauli-Z expectation pooled by mean",
                    "is_noisy": bool(estimator.is_noisy),
                    "backend_type": backend_type
                }
            except Exception as e:
                qml_config = {
                    "n_qubits": X_train.shape[1],
                    "n_layers": layers,
                    "encoding_method": encoding_method,
                    "feature_to_qubit": {name: index for index, name in enumerate(processed["feature_names"])},
                    "variational_gate": variational_gate,
                    "entanglement_strategy": entanglement_strategy,
                    "measurement": "Pauli-Z expectation pooled by mean",
                    "is_noisy": is_noisy_quantum,
                    "backend_type": backend_type
                }

        trained_model.configuration["quantum_config"] = qml_config
        trained_model.configuration["metrics"]["balanced_accuracy"] = metrics["balanced_accuracy"]
        trained_model.configuration["metrics"]["inference_duration_ms"] = inference_duration_ms
        await self.model_repo.update(trained_model)

        run = await self.training_repo.create(TrainingRun(
            user_id=user_id, model_id=str(trained_model.id), dataset_version_id=str(version.id),
            feature_selection_run_id=str(feature_run.id),
            preprocessing_run_id=str(preprocessing_run.id) if preprocessing_run else None,
            learning_type="QML" if template.model_type == "vqc" else "CML",
            model_type=template.model_type,
            status="completed", metrics=metrics,
            model_parameters={
                "parameter_count": int(X_train.shape[1] * layers + 1) if template.model_type == "vqc" else None,
            },
            training_config={
                "hyperparameters": hyperparameters,
                "random_state": 42,
                "is_noisy_quantum": is_noisy_quantum,
                "noise_params": noise_params,
            },
            feature_config={"selected_features": features, "target_column": target},
            qml_config=qml_config
        ))
        trained_model.training_run_id = str(run.id)
        await self.model_repo.update(trained_model)
        await Evaluation(
            user_id=user_id, model_id=str(trained_model.id), dataset_version_id=str(version.id),
            accuracy=accuracy, precision=precision, recall=sensitivity, f1_score=f1,
            roc_auc=auc, confusion_matrix=[tn, fp, fn, tp], metrics_json=metrics,
        ).insert()

        experiment = await Experiment(
            user_id=user_id, name=f"{dataset_name} · {version.version_tag} · {template.name}",
            description="Dataset-driven model training with the selected preprocessing and feature-selection runs.",
            tags=["uploaded-dataset", template.model_type], dataset_id=str(version.dataset_id),
            dataset_version_id=str(version.id), dataset_name=dataset_name,
            preprocessing_run_id=str(preprocessing_run.id) if preprocessing_run else None,
            feature_selection_run_id=str(feature_run.id), target_column=target,
            selected_features=features, training_run_ids=[str(run.id)],
        ).insert()
        run.experiment_id = str(experiment.id)
        return await self.training_repo.update(run)

    @staticmethod
    def _default_plan_steps(df: pd.DataFrame, features: list[str]) -> list[PreprocessingPlanStep]:
        numeric = [column for column in features if pd.api.types.is_numeric_dtype(df[column]) and not pd.api.types.is_bool_dtype(df[column])]
        categorical = [column for column in features if column not in numeric]
        steps = [PreprocessingPlanStep(
            step_id=1, tool_name="stratified_split", rationale="Split uploaded rows before fitting transformations.",
            parameters={"train_ratio": .70, "val_ratio": .15, "test_ratio": .15, "random_state": 42}, fit_on_train_only=False,
        )]
        if numeric:
            steps.extend([
                PreprocessingPlanStep(step_id=len(steps) + 1, tool_name="median_imputer", rationale="Use training-only numeric medians.", parameters={"strategy": "median", "columns": numeric}),
                PreprocessingPlanStep(step_id=len(steps) + 2, tool_name="min_max_scaler", rationale="Use numeric ranges from training rows only.", parameters={"columns": numeric}),
            ])
        if categorical:
            steps.extend([
                PreprocessingPlanStep(step_id=len(steps) + 1, tool_name="most_frequent_imputer", rationale="Use training-only categorical modes.", parameters={"columns": categorical}),
                PreprocessingPlanStep(step_id=len(steps) + 2, tool_name="one_hot_encoder", rationale="Encode observed categorical values.", parameters={"columns": categorical}),
            ])
        return steps


def _positive_class_probabilities(estimator: Any, values: np.ndarray) -> np.ndarray:
    """Return the probability for encoded positive class 1 from wrapped or raw sklearn models."""
    probabilities = np.asarray(estimator.predict_proba(values), dtype=float)
    if probabilities.ndim == 1:
        return probabilities
    classes = np.asarray(getattr(estimator, "classes_", np.arange(probabilities.shape[1])))
    positive_indices = np.flatnonzero(classes == 1)
    positive_index = int(positive_indices[0]) if positive_indices.size else probabilities.shape[1] - 1
    return probabilities[:, positive_index]
