"""
Application configuration using Pydantic Settings.

All environment variables are validated on import.
Secret values (API keys) are masked in logs.
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Cohere API
    cohere_api_key: str = Field(..., description="Cohere API key for embeddings and generation")

    # Qdrant Cloud (optional - can use local or skip for now)
    qdrant_url: Optional[str] = Field(default="http://localhost:6333", description="Qdrant cluster URL")
    qdrant_api_key: Optional[str] = Field(default=None, description="Qdrant API key")
    qdrant_cluster_id: Optional[str] = Field(default="local", description="Qdrant cluster ID")

    # Neon Serverless Postgres (support both NEON_DB_URL and DATABASE_URL)
    neon_db_url: Optional[str] = Field(default=None, description="Neon Postgres connection string")
    database_url: Optional[str] = Field(default=None, description="Alternative database URL")

    # Application config
    log_level: str = Field(default="INFO", description="Logging level")
    max_concurrent_requests: int = Field(
        default=100, ge=1, le=1000, description="Max concurrent requests"
    )
    rate_limit_per_minute: int = Field(
        default=100, ge=1, le=10000, description="Rate limit per IP per minute"
    )

    # Server config (optional)
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")

    # Admin API key (optional - for ingestion endpoint)
    admin_api_key: str = Field(default=None, description="Admin API key for ingestion")

    @property
    def db_url(self) -> str:
        """Get database URL from either neon_db_url or database_url."""
        return self.neon_db_url or self.database_url or ""

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the standard Python logging levels."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()

    def mask_secret(self, value: str) -> str:
        """Mask secret values for logging (show first 4 chars only)."""
        if len(value) <= 8:
            return "***"
        return f"{value[:4]}...{value[-4:]}"

    def get_masked_config(self) -> dict[str, str]:
        """Get configuration with secrets masked for safe logging."""
        return {
            "cohere_api_key": self.mask_secret(self.cohere_api_key),
            "qdrant_url": self.qdrant_url,
            "qdrant_api_key": self.mask_secret(self.qdrant_api_key),
            "qdrant_cluster_id": self.qdrant_cluster_id,
            "neon_db_url": self.mask_secret(self.neon_db_url),
            "log_level": self.log_level,
            "max_concurrent_requests": str(self.max_concurrent_requests),
            "rate_limit_per_minute": str(self.rate_limit_per_minute),
            "host": self.host,
            "port": str(self.port),
        }


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    This function is cached to ensure settings are loaded only once
    and reused across the application.
    """
    return Settings()


# Singleton instance for direct import
settings = get_settings()
