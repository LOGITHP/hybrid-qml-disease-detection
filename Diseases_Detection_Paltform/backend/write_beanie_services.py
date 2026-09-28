import os

services_dir = r"c:\Users\logit\Downloads\hybrid-qml-disease-detection\Diseases_Detection_Paltform\backend\app\services"

def write_file(filename, content):
    with open(os.path.join(services_dir, filename), "w") as f:
        f.write(content)

write_file("user_service.py", '''"""User Service."""
from app.repositories.user_repository import UserRepository
from app.database.models.user import User

class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
        
    async def get_user(self, user_id: str) -> User:
        return await self.user_repo.get_by_id(user_id)
''')

write_file("auth_service.py", '''"""Auth Service."""
from app.repositories.user_repository import UserRepository
from app.database.models.user import User
from app.core.security import verify_password, get_password_hash, create_access_token
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
            password_hash=get_password_hash(request_data.password),
            full_name=request_data.full_name,
            role=request_data.role
        )
        return await self.user_repo.create(user)
        
    async def login(self, request_data):
        user = await self.user_repo.get_by_email(request_data.email)
        if not user or not verify_password(request_data.password, user.password_hash):
            raise AuthenticationError("Invalid email or password.")
            
        access_token = create_access_token(data={"sub": str(user.id)})
        return {"access_token": access_token, "token_type": "bearer", "refresh_token": "dummy"}
        
    async def refresh_token(self, token):
        # Stub
        pass
''')

write_file("dataset_service.py", '''"""Dataset Service."""
from app.repositories.dataset_repository import DatasetRepository
from app.database.models.dataset import Dataset, DatasetVersion

class DatasetService:
    def __init__(self, dataset_repo: DatasetRepository):
        self.dataset_repo = dataset_repo
        
    async def get_datasets(self, user_id: str):
        return await self.dataset_repo.list_by_user(user_id)
        
    async def create_dataset(self, user_id: str, name: str, description: str = None):
        dataset = Dataset(user_id=user_id, name=name, description=description)
        return await self.dataset_repo.create(dataset)
''')

write_file("model_service.py", '''"""Model Service."""
from app.repositories.model_repository import ModelRepository
from app.database.models.model import Model

class ModelService:
    def __init__(self, model_repo: ModelRepository):
        self.model_repo = model_repo
        
    async def get_models(self, user_id: str):
        return await self.model_repo.list_by_user(user_id)
        
    async def create_model(self, user_id: str, name: str, algorithm: str, is_quantum: bool):
        model = Model(user_id=user_id, name=name, algorithm=algorithm, is_quantum=is_quantum)
        return await self.model_repo.create(model)
''')

print("Created Beanie services successfully.")
