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

    # PostgreSQL Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgrespassword@localhost:5432/hybrid_qml_db",
        description="Async database connection URI",
    )

    # Redis URL
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis connection URI")

    # Artifact storage
    ARTIFACT_ROOT: str = Field(default="./artifacts", description="Local filesystem path for artifact storage")

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
    LLM_PROVIDER: str = Field(default="gemini", description="Default LLM provider")
    LLM_MODEL: str = Field(default="gemini-1.5-flash", description="Default model identifier")
    GEMINI_API_KEY: str = Field(default="", description="API key for Gemini LLM provider (optional in Phase 1)")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
