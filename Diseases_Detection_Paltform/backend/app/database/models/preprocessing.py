"""Preprocessing ODM model."""
from typing import Optional, Dict, Any, List
from beanie import Document
from pydantic import Field
from datetime import datetime, timezone

class PreprocessingRun(Document):
    dataset_version_id: str
    user_id: str
    status: str = "running"
    config_params: Dict[str, Any] = Field(default_factory=dict)
    
    # Preprocessing Artifact fields
    is_ready_for_training: bool = False
    artifact_storage_path: Optional[str] = None
    target_column: Optional[str] = None
    target_mapping: Optional[Dict[str, int]] = None
    original_feature_count: Optional[int] = None
    final_feature_count: Optional[int] = None
    final_feature_names: Optional[List[str]] = None
    
    scaler_artifact_id: Optional[str] = None
    imputer_artifact_id: Optional[str] = None
    encoder_artifact_id: Optional[str] = None
    ai_recommendation_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "preprocessing_runs"


class PreprocessingArtifact(Document):
    """Immutable artifact capturing the complete state and execution results of a preprocessing pipeline."""
    dataset_id: str
    dataset_version_id: str
    preprocessing_run_id: str
    user_id: str
    pipeline_version: int = 1
    
    pipeline_config: Dict[str, Any]
    
    original_features: List[str]
    selected_features: Optional[List[str]] = None
    final_features: List[str]
    
    target_column: str
    target_mapping: Optional[Dict[str, int]] = None
    
    train_split_metadata: Dict[str, Any] = Field(default_factory=dict)
    validation_split_metadata: Dict[str, Any] = Field(default_factory=dict)
    test_split_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    feature_schema: Dict[str, str] = Field(default_factory=dict)
    final_feature_count: int
    
    output_dataset_location: str
    artifact_storage_path: str
    
    random_seed: int = 42
    library_versions: Dict[str, str] = Field(default_factory=dict)
    status: str = "ready"
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "preprocessing_artifacts"
