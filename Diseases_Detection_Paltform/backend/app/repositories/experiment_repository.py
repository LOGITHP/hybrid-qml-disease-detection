"""MongoDB Experiment Repository using Beanie."""
from typing import List, Optional
from app.database.models.experiment import Experiment

class ExperimentRepository:
    async def get_by_id(self, exp_id: str) -> Optional[Experiment]:
        return await Experiment.get(exp_id)
        
    async def list_by_user(self, user_id: str) -> List[Experiment]:
        return await Experiment.find(Experiment.user_id == user_id).to_list()
        
    async def create(self, exp: Experiment) -> Experiment:
        return await exp.insert()
