"""Application configuration managed via Pydantic settings."""

from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings loaded from environment variables or .env file."""

    # Project metadata
    PROJECT_NAME: str = "Hybrid Quantum Machine Learning Platform API"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = Field(default="development", description="Runtime environment: development, testing, production")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # Server binding
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # MongoDB Database
    MONGODB_URL: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection URI",
    )
    MONGODB_DB: str = Field(default="hybrid_qml_db", description="MongoDB database name")

    # Redis URL
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis connection URI")

    # MinIO Storage
    MINIO_URL: str = Field(default="http://localhost:9000", description="MinIO endpoint URL")
    MINIO_ACCESS_KEY: str = Field(default="minioadmin", description="MinIO access key")
    MINIO_SECRET_KEY: str = Field(default="minioadmin", description="MinIO secret key")
    MINIO_BUCKET_NAME: str = Field(default="hybrid-qml-artifacts", description="MinIO default bucket")

    # Security & JWT
    JWT_SECRET: str = Field(
        default="temporary_development_secret_key_change_in_production_32_bytes_min!",
        description="Secret key for JWT generation and verification",
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, description="Access token expiration in minutes")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiration in days")

    # CORS configuration
    CORS_ORIGINS: Union[List[str], str] = Field(
        default=["http://localhost:3000", "http://localhost:5173", "http://localhost:8000"],
        description="Allowed CORS origins list or comma-separated string",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Union[List[str], str]) -> List[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    # AI Preprocessing Agent LLM Provider Configuration
    LLM_PROVIDER: str = Field(default="ollama", description="Default LLM provider")
    LLM_BASE_URL: str = Field(default="http://localhost:11434", description="Ollama API base URL")

    # Local Artifacts Storage (if MinIO is not used directly or fallback)
    ARTIFACT_ROOT: str = Field(default="/app/artifacts", description="Root directory for local artifact storage")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
