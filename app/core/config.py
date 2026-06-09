from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TopConf Paper Hub"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./topconf_papers.db"
    redis_url: str = "redis://localhost:6379/0"
    conference_config_path: str = "configs/conferences/top_conferences.yaml"
    taxonomy_config_path: str = "configs/taxonomy/tags.yaml"
    request_timeout_seconds: int = 20
    crawler_user_agent: str = "TopConfPaperHub/0.1 (+metadata-only academic crawler)"
    default_year_window: int = Field(default=5, ge=1, le=50)
    scheduler_enabled: bool = False
    scheduler_hour_utc: int = Field(default=2, ge=0, le=23)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

