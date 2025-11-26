from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application configuration loaded from environment variables.

    Values can be supplied via environment variables or a local `.env` file.
    Defaults are provided so the application can still boot with minimal
    configuration, but sensitive values (API keys, Supabase credentials, etc.)
    should always be supplied via the environment in production.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # OpenAI configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: Optional[str] = None
    LAZY_MODEL: str = "gpt-3.5-turbo"
    PRO_MODEL: str = "gpt-4o"
    LAZY_MAX_TOKENS: int = 512
    PRO_MAX_TOKENS: int = 2048
    LAZY_TEMPERATURE: float = 0.3
    PRO_TEMPERATURE: float = 0.7

    # Supabase configuration
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None

    # Redis configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings getter so the configuration is only loaded once per process.
    """

    return Settings()  # type: ignore[arg-type]


settings = get_settings()

