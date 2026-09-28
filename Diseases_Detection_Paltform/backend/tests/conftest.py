"""Pytest fixtures for unit and integration testing."""

import asyncio
import os
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

# Set testing environment variables before importing app
os.environ["ENVIRONMENT"] = "testing"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["MONGODB_URL"] = "mongodb://localhost:27017"
os.environ["MONGODB_DB"] = "test_db"
os.environ["JWT_SECRET"] = "test_super_secret_key_at_least_32_bytes_long_12345!"
os.environ["ARTIFACT_ROOT"] = "./test_artifacts"

import app.database.session as session_mod
from beanie import init_beanie
from app.database.models import __all__ as all_models_names
import importlib
from app.main import app

@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_beanie():
    """Mock MongoDB Client using mongomock-motor for isolated tests."""
    mock_client = AsyncMongoMockClient()
    db = mock_client[os.environ["MONGODB_DB"]]
    
    # Override global client in session so application uses mock
    session_mod.client = mock_client
    
    # Init beanie
    models_module = importlib.import_module("app.database.models")
    document_models = [getattr(models_module, model_name) for model_name in all_models_names]
    await init_beanie(database=db, document_models=document_models)
    
    yield
    
    # Teardown database collections
    for coll_name in await db.list_collection_names():
        await db[coll_name].drop()


@pytest_asyncio.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Test HTTP client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
