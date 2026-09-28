"""Model Service."""
from app.repositories.model_repository import ModelRepository
from app.database.models.model import Model
from app.core.exceptions import ResourceNotFoundError

class ModelService:
    def __init__(self, model_repo: ModelRepository = None):
        self.model_repo = model_repo or ModelRepository()
        
    async def list_user_models(self, user_id: str):
        return await self.model_repo.list_by_user(user_id)
        
    async def register_model(self, user_id: str, name: str, model_type: str, description: str, is_default: bool = False):
        model = Model(
            user_id=user_id, 
            name=name, 
            model_type=model_type, 
            description=description, 
            is_default=is_default,
            status="pending"
        )
        return await self.model_repo.create(model)

    async def get_model(self, model_id: str, user_id: str, is_admin: bool = False):
        model = await self.model_repo.get_by_id(model_id)
        if not model:
            raise ResourceNotFoundError("Model", model_id)
        if model.user_id != user_id and not model.is_default and not is_admin:
            raise ResourceNotFoundError("Model", model_id)
        return model

    async def seed_default_models(self):
        defaults = [
            Model(user_id="system", name="Linear SVM Tabular Baseline", model_type="svm_linear", description="Built-in tabular baseline. The estimator is trained on the selected uploaded dataset.", is_default=True, status="active"),
            Model(user_id="system", name="RBF SVM Tabular Baseline", model_type="svm_rbf", description="Built-in non-linear tabular baseline. The estimator is trained on the selected uploaded dataset.", is_default=True, status="active"),
            Model(user_id="system", name="PennyLane VQC", model_type="vqc", description="Built-in variational quantum classifier trained on the selected uploaded dataset.", is_default=True, status="active"),
        ]
        results = []
        for d in defaults:
            # Upsert or ignore
            existing = await Model.find_one({"name": d.name, "user_id": "system", "is_default": True})
            if not existing:
                res = await self.model_repo.create(d)
                results.append(res)
            else:
                existing.model_type = d.model_type
                existing.description = d.description
                existing.is_default = True
                existing.status = "active"
                await self.model_repo.update(existing)
                results.append(existing)
        return results

    async def compare_selected_models(self, user_id: str, model_ids: list, model_version_ids: list, is_admin: bool = False):
        # Mock comparison for simplified architecture
        return {
            "overall_accuracy_leader": "vqc",
            "f1_score_leader": "vqc",
            "training_speed_leader": "svm_linear",
            "qml_advantage_detected": True,
            "comparisons": []
        }
