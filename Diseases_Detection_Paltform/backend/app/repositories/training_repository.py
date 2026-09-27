"""Training run repository."""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.training import TrainingRun, TrainingConfig
from app.database.models.evaluation import EvaluationRun
from app.database.models.prediction import PredictionRun


class TrainingRepository:
    """Data access repository for TrainingConfigs, TrainingRuns, EvaluationRuns, and PredictionRuns."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_training_run(self, run: TrainingRun) -> TrainingRun:
        """Persist a new training run."""
        self.session.add(run)
        await self.session.flush()
        await self.session.refresh(run)
        return run

    async def get_training_run(self, run_id: str, user_id: Optional[str] = None) -> Optional[TrainingRun]:
        """Fetch training run by ID."""
        query = select(TrainingRun).where(TrainingRun.id == run_id)
        if user_id is not None:
            query = query.where(TrainingRun.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_runs_by_user(self, user_id: str, skip: int = 0, limit: int = 50) -> List[TrainingRun]:
        """List training runs for a user."""
        query = select(TrainingRun).where(TrainingRun.user_id == user_id).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create_evaluation_run(self, eval_run: EvaluationRun) -> EvaluationRun:
        """Persist model evaluation results."""
        self.session.add(eval_run)
        await self.session.flush()
        await self.session.refresh(eval_run)
        return eval_run

    async def create_prediction_run(self, pred_run: PredictionRun) -> PredictionRun:
        """Persist an inference prediction run."""
        self.session.add(pred_run)
        await self.session.flush()
        await self.session.refresh(pred_run)
        return pred_run
