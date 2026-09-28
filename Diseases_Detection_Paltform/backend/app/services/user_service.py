"""User Service."""
from app.repositories.user_repository import UserRepository
from app.database.models.user import User

class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
        
    async def get_user(self, user_id: str) -> User:
        return await self.user_repo.get_by_id(user_id)
