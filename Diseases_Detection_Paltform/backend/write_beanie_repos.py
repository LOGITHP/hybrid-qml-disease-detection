import os

repos_dir = r"c:\Users\logit\Downloads\hybrid-qml-disease-detection\Diseases_Detection_Paltform\backend\app\repositories"

def write_file(filename, content):
    with open(os.path.join(repos_dir, filename), "w") as f:
        f.write(content)

write_file("user_repository.py", '''"""MongoDB User Repository using Beanie."""
from typing import Optional
from beanie.operators import RegEx
from app.database.models.user import User

class UserRepository:
    async def get_by_id(self, user_id: str) -> Optional[User]:
        return await User.get(user_id)
        
    async def get_by_email(self, email: str) -> Optional[User]:
        return await User.find_one(User.email == email)
        
    async def create(self, user: User) -> User:
        return await user.insert()
''')

write_file("dataset_repository.py", '''"""MongoDB Dataset Repository using Beanie."""
from typing import List, Optional
from beanie.operators import In
from app.database.models.dataset import Dataset, DatasetVersion

class DatasetRepository:
    async def get_by_id(self, dataset_id: str) -> Optional[Dataset]:
        return await Dataset.get(dataset_id)
        
    async def list_by_user(self, user_id: str) -> List[Dataset]:
        return await Dataset.find(Dataset.user_id == user_id).to_list()
        
    async def create(self, dataset: Dataset) -> Dataset:
        return await dataset.insert()
        
    async def get_version(self, version_id: str) -> Optional[DatasetVersion]:
        return await DatasetVersion.get(version_id)
        
    async def create_version(self, version: DatasetVersion) -> DatasetVersion:
        return await version.insert()
        
    async def list_versions(self, dataset_id: str) -> List[DatasetVersion]:
        return await DatasetVersion.find(DatasetVersion.dataset_id == dataset_id).to_list()
''')

write_file("model_repository.py", '''"""MongoDB Model Repository using Beanie."""
from typing import List, Optional
from app.database.models.model import Model

class ModelRepository:
    async def get_by_id(self, model_id: str) -> Optional[Model]:
        return await Model.get(model_id)
        
    async def list_by_user(self, user_id: str) -> List[Model]:
        return await Model.find(Model.user_id == user_id).to_list()
        
    async def create(self, model: Model) -> Model:
        return await model.insert()
        
    async def update(self, model: Model) -> Model:
        return await model.save()
''')

write_file("training_repository.py", '''"""MongoDB Training Repository using Beanie."""
from typing import List, Optional
from app.database.models.training import TrainingRun

class TrainingRepository:
    async def get_by_id(self, run_id: str) -> Optional[TrainingRun]:
        return await TrainingRun.get(run_id)
        
    async def create(self, run: TrainingRun) -> TrainingRun:
        return await run.insert()
        
    async def update(self, run: TrainingRun) -> TrainingRun:
        return await run.save()
''')

write_file("experiment_repository.py", '''"""MongoDB Experiment Repository using Beanie."""
from typing import List, Optional
from app.database.models.experiment import Experiment

class ExperimentRepository:
    async def get_by_id(self, exp_id: str) -> Optional[Experiment]:
        return await Experiment.get(exp_id)
        
    async def list_by_user(self, user_id: str) -> List[Experiment]:
        return await Experiment.find(Experiment.user_id == user_id).to_list()
        
    async def create(self, exp: Experiment) -> Experiment:
        return await exp.insert()
''')

print("Created Beanie repositories successfully.")
