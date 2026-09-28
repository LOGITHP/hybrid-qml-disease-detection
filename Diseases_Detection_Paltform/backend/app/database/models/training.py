"""Training ODM."""
from typing import Optional, Dict, Any
from beanie import Document
from pydantic import Field
from datetime import datetime, timezone
import uuid

class TrainingRun(Document):
    model_id: Optional[str] = None
    learning_type: str = "CML"  # "CML" or "QML"
    model_type: str = "SVM"     # "SVM" or "VQC"
    dataset_version_id: str
    user_id: str
    feature_selection_run_id: Optional[str] = None
    preprocessing_run_id: Optional[str] = None
    preprocessing_artifact_id: Optional[str] = None
    experiment_id: str = Field(default_factory=lambda: f"EXP-{uuid.uuid4().hex[:8].upper()}")
    
    # Configurations
    feature_config: Dict[str, Any] = Field(default_factory=dict)
    model_config: Optional[Dict[str, Any]] = None
    qml_config: Optional[Dict[str, Any]] = None
    training_config: Dict[str, Any] = Field(default_factory=dict)
    
    metrics: Optional[Dict[str, Any]] = None
    status: str = "running"
    epochs: Optional[int] = None
    batch_size: Optional[int] = None
    learning_rate: Optional[float] = None
    optimizer: Optional[str] = None
    current_epoch: Optional[int] = 0
    loss_history: Optional[list] = None
    final_loss: Optional[float] = None
    execution_time_seconds: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "training_runs"
