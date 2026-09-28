"""MongoDB Model Repository using Beanie."""
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

    async def list_defaults(self) -> List[Model]:
        return await Model.find(Model.is_default == True).to_list()

