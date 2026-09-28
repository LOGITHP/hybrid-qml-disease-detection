"""Database engine and async session dependency using Motor and Beanie."""

from typing import AsyncGenerator
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

# Global MongoDB client
client: AsyncIOMotorClient = None


def get_db_client() -> AsyncIOMotorClient:
    """Return the global MongoDB client."""
    global client
    if client is None:
        client = AsyncIOMotorClient(settings.MONGODB_URL)
    return client


async def get_db():
    """Dependency for obtaining an asynchronous database session/client."""
    db_client = get_db_client()
    yield db_client[settings.MONGODB_DB]
