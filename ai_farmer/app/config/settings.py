"""Application configuration using Pydantic Settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Production-grade configuration for AI Farmer."""

    # App
    app_name: str = Field(default="AI Farmer", alias="APP_NAME")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    secret_key: str = Field(default="dev-secret-key", alias="SECRET_KEY")

    # LLM
    ai_provider: str = Field(default="auto", alias="AI_PROVIDER")
    ai_model: Optional[str] = Field(default=None, alias="AI_MODEL")
    ai_api_key: Optional[str] = Field(default=None, alias="AI_API_KEY")
    ai_base_url: Optional[str] = Field(default=None, alias="AI_BASE_URL")
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    groq_api_key: Optional[str] = Field(default=None, alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_MODEL")
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    openrouter_api_key: Optional[str] = Field(default=None, alias="OPENROUTER_API_KEY")
    ollama_base_url: str = Field(default="http://localhost:11434/v1", alias="OLLAMA_BASE_URL")

    # External APIs
    weather_api_key: Optional[str] = Field(default=None, alias="WEATHER_API_KEY")
    market_api_key: Optional[str] = Field(default=None, alias="MARKET_API_KEY")
    gov_scheme_api_url: str = Field(default="", alias="GOV_SCHEME_API_URL")
    soil_test_api_url: str = Field(default="", alias="SOIL_TEST_API_URL")

    # Paths
    database_url: str = Field(default="sqlite:///./data/ai_farmer.db", alias="DATABASE_URL")
    model_path: str = Field(default="./data/models", alias="MODEL_PATH")
    data_path: str = Field(default="./data", alias="DATA_PATH")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
