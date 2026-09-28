"""Model ODM."""
from typing import Optional, Dict, Any
from beanie import Document
from pydantic import Field
from datetime import datetime, timezone

class Model(Document):
    user_id: str
    name: str
    description: Optional[str] = None
    model_type: str = "classical"
    algorithm: str = "svm"
    status: str = "created"
    is_quantum: bool = False
    is_default: bool = False
    configuration: Dict[str, Any] = Field(default_factory=dict)
    trained_weights_artifact_id: Optional[str] = None
    training_run_id: Optional[str] = None
    evaluation_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "models"
