"""Training ODM."""
from typing import Optional, Dict, Any
from beanie import Document
from pydantic import Field
from datetime import datetime, timezone

class TrainingRun(Document):
    model_id: str
    dataset_version_id: str
    user_id: str
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
