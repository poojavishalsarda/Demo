"""Application settings and configuration."""
import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment or .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "BookstoreAgentBackend"
    APP_ENV: str = "development"
    DEBUG: bool = True
    
    # Network Security: Bind only to localhost / 127.0.0.1
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./bookstore.db"
    
    # Security
    SECRET_KEY: str = Field(default="dev-secret-key-replace-in-production")
    ALLOWED_ORIGINS: List[str] = [
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://127.0.0.1:8000",
    ]
    
    # Agent & LLM Integration
    AGENT_MODEL_PROVIDER: str = "mock"  # 'mock', 'watsonx', 'openai', etc.
    LLM_API_KEY: str = ""
    LLM_MODEL_NAME: str = "granite-3-8b-instruct"
    MAX_AGENT_ITERATIONS: int = 6


settings = Settings()
