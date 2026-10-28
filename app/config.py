from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import HttpUrl


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    DATABASE_URL: str
    LINK_TTL_DAYS: int
    BASE_URL: HttpUrl


@lru_cache
def get_settings() -> Settings:
    return Settings()
