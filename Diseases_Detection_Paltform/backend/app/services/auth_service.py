"""Auth Service."""
from app.repositories.user_repository import UserRepository
from app.database.models.user import User
from app.core.security import verify_password, hash_password, create_access_token
from app.core.exceptions import AuthenticationError

class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
        
    async def register(self, request_data) -> User:
        existing = await self.user_repo.get_by_email(request_data.email)
        if existing:
            raise AuthenticationError("Email already registered.")
        
        user = User(
            email=request_data.email,
            password_hash=hash_password(request_data.password),
            full_name=request_data.full_name
        )
        return await self.user_repo.create(user)
        
    async def login(self, request_data):
        user = await self.user_repo.get_by_email(request_data.email)
        if not user or not verify_password(request_data.password, user.password_hash):
            raise AuthenticationError("Invalid email or password.")
            
        access_token = create_access_token(user_id=str(user.id), role=user.role)
        from app.core.config import settings
        return {
            "access_token": access_token, 
            "token_type": "bearer", 
            "refresh_token": "dummy",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": user
        }
        
    async def refresh_token(self, token):
        # Stub
        pass
