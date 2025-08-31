from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    MAX_TOKENS: int = 1000
    TEMPERATURE: float = 0.7
    LAZY_MODEL: str = "gpt-3.5-turbo"
    PRO_MODEL: str = "gpt-4o"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()