"""MongoDB Training Repository using Beanie."""
from typing import List, Optional
from app.database.models.training import TrainingRun

class TrainingRepository:
    async def get_by_id(self, run_id: str) -> Optional[TrainingRun]:
        return await TrainingRun.get(run_id)
        
    async def create(self, run: TrainingRun) -> TrainingRun:
        return await run.insert()
        
    async def update(self, run: TrainingRun) -> TrainingRun:
        return await run.save()
