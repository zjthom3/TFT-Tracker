from functools import lru_cache
from typing import Sequence

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env",), env_prefix="TFT_", case_sensitive=False)

    api_title: str = "TFT Tracker API"
    api_version: str = "0.1.0"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/tft_tracker"
    ingest_tickers: Sequence[str] = ("NVDA", "BTC-USD")
    ingest_window_days: int = 7
    ingest_interval_minutes: int = 1
    allowed_origins: Sequence[str] = (
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
