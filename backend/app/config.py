"""Application configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # App
    app_name: str = "Scribe API"
    debug: bool = False

    # Database (SQLite for development, PostgreSQL for production)
    database_url: str = "sqlite:///./scribe.db"

    # Auth
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # LLM
    anthropic_api_key: str = ""

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings."""
    return Settings()
