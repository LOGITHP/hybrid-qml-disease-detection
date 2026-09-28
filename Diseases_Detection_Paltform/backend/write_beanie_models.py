import os

models_dir = r"c:\Users\logit\Downloads\hybrid-qml-disease-detection\Diseases_Detection_Paltform\backend\app\database\models"

def write_file(filename, content):
    with open(os.path.join(models_dir, filename), "w") as f:
        f.write(content)

write_file("user.py", '''"""User ODM database model."""
from typing import Optional
from beanie import Document
from pydantic import EmailStr, Field
from datetime import datetime, timezone

class User(Document):
    email: EmailStr
    password_hash: str
    full_name: Optional[str] = None
    role: str = "user"
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "users"
        indexes = ["email"]
''')

write_file("dataset.py", '''"""Dataset ODM database model."""
from typing import Optional, Dict, Any
from beanie import Document, Link
from pydantic import Field
from datetime import datetime, timezone
from app.database.models.user import User

class Dataset(Document):
    user_id: str
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "datasets"

class DatasetVersion(Document):
    dataset_id: str
    user_id: str
    version_tag: str
    file_artifact_id: Optional[str] = None
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    status: str = "uploaded"
    dataset_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "dataset_versions"
''')

write_file("preprocessing.py", '''"""Preprocessing ODM model."""
from typing import Optional, Dict, Any
from beanie import Document
from pydantic import Field
from datetime import datetime, timezone

class PreprocessingRun(Document):
    dataset_version_id: str
    user_id: str
    status: str = "running"
    config_params: Dict[str, Any] = Field(default_factory=dict)
    imputation_strategy: Optional[str] = None
    scaling_strategy: Optional[str] = None
    encoding_strategy: Optional[str] = None
    output_dataset_version_id: Optional[str] = None
    scaler_artifact_id: Optional[str] = None
    imputer_artifact_id: Optional[str] = None
    encoder_artifact_id: Optional[str] = None
    ai_recommendation_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "preprocessing_runs"
''')

write_file("feature_selection.py", '''"""Feature Selection ODM model."""
from typing import Optional, Dict, Any, List
from beanie import Document
from pydantic import Field
from datetime import datetime, timezone

class FeatureSelectionRun(Document):
    dataset_version_id: str
    user_id: str
    status: str = "running"
    method: str = "mutual_information"
    num_features: int
    selected_features: Optional[List[str]] = None
    feature_scores: Optional[Dict[str, float]] = None
    output_dataset_version_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "feature_selection_runs"
''')

write_file("model.py", '''"""Model ODM."""
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
    configuration: Dict[str, Any] = Field(default_factory=dict)
    trained_weights_artifact_id: Optional[str] = None
    training_run_id: Optional[str] = None
    evaluation_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "models"
''')

write_file("quantum.py", '''"""Quantum config ODM."""
from typing import Optional, Dict, Any
from beanie import Document
from pydantic import Field
from datetime import datetime, timezone

class QuantumConfiguration(Document):
    model_id: str
    n_qubits: int = 4
    n_layers: int = 2
    ansatz: str = "strongly_entangling"
    data_encoding: str = "angle"
    backend: str = "default.qubit"
    noise_model: Optional[str] = None
    shots: Optional[int] = None
    measurement: str = "pauli_z"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "quantum_configurations"
''')

write_file("training.py", '''"""Training ODM."""
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
''')

write_file("evaluation.py", '''"""Evaluation ODM."""
from typing import Optional, Dict, Any
from beanie import Document
from pydantic import Field
from datetime import datetime, timezone

class Evaluation(Document):
    model_id: str
    dataset_version_id: str
    user_id: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: Optional[float] = None
    confusion_matrix: Optional[list] = None
    metrics_json: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "evaluations"
''')

write_file("prediction.py", '''"""Prediction ODM."""
from typing import Optional, Dict, Any
from beanie import Document
from pydantic import Field
from datetime import datetime, timezone

class Prediction(Document):
    model_id: str
    user_id: str
    input_data: Dict[str, Any] = Field(default_factory=dict)
    prediction_result: float
    probability: Optional[float] = None
    risk_score: Optional[float] = None
    decision_threshold: Optional[float] = 0.5
    explanation_json: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[float] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "predictions"
''')

write_file("artifact.py", '''"""Artifact ODM."""
from typing import Optional
from beanie import Document
from pydantic import Field
from datetime import datetime, timezone

class Artifact(Document):
    user_id: str
    filename: str
    file_path: str
    file_type: str = "csv"
    size_bytes: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "artifacts"
''')

write_file("experiment.py", '''"""Experiment ODM."""
from typing import Optional
from beanie import Document
from pydantic import Field
from datetime import datetime, timezone

class Experiment(Document):
    user_id: str
    name: str
    description: Optional[str] = None
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "experiments"
''')

write_file("audit.py", '''"""Audit Log ODM."""
from typing import Optional, Dict, Any
from beanie import Document
from pydantic import Field
from datetime import datetime, timezone

class AuditLog(Document):
    user_id: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "audit_logs"
''')

write_file("__init__.py", '''"""MongoDB Document Models for Beanie."""
from .user import User
from .dataset import Dataset, DatasetVersion
from .preprocessing import PreprocessingRun
from .feature_selection import FeatureSelectionRun
from .model import Model
from .quantum import QuantumConfiguration
from .training import TrainingRun
from .evaluation import Evaluation
from .prediction import Prediction
from .artifact import Artifact
from .experiment import Experiment
from .audit import AuditLog

__all__ = [
    "User", "Dataset", "DatasetVersion", "PreprocessingRun",
    "FeatureSelectionRun", "Model", "QuantumConfiguration",
    "TrainingRun", "Evaluation", "Prediction", "Artifact",
    "Experiment", "AuditLog"
]
''')

print("Created Beanie models successfully.")
