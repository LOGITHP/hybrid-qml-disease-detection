"""MongoDB User Repository using Beanie."""
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
