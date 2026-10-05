"""Core application configuration."""
import os
from pathlib import Path
from typing import List, Union
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory for the backend (vibe-trader-ai)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    APP_NAME: str = "Vibe Trader AI"
    DEBUG: bool = True

    # Server settings
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    CHAT_OLLAMA_HOST: str = "http://127.0.0.1:11434"
    CHAT_OLLAMA_MODEL: str = "qwen3-local:latest"
    CHAT_TIMEOUT_SECONDS: float = 50.0
    # News retrieval is a server-side tool, independent of local model inference.
    NEWS_PROVIDER: str = "ollama_local"
    NEWS_API_KEY: SecretStr = SecretStr("")
    NEWS_TIMEOUT_SECONDS: float = Field(8.0, ge=1, le=30)
    NEWS_RETRIES: int = Field(1, ge=0, le=2)
    NEWS_CACHE_TTL_SECONDS: int = Field(120, ge=0, le=900)
    NEWS_MAX_AGE_HOURS: int = Field(72, ge=1, le=168)
    NEWS_MAX_ARTICLES: int = Field(3, ge=1, le=5)
    API_V1_PREFIX: str = "/api"

    # CORS settings - strictly restricted to local origins for security
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Database settings (SQLite local-first)
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'data' / 'vibe_trader.db'}"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, tuple)):
            return [str(i) for i in v]
        return ["http://localhost:5173", "http://127.0.0.1:5173"]

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
