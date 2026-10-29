from functools import lru_cache

from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    DATABASE_URL: str
    LINK_TTL_DAYS: int
    BASE_URL: HttpUrl


@lru_cache
def get_settings() -> Settings:
    return Settings()
