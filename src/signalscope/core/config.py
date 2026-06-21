"""Runtime configuration with safe local defaults."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration sourced from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SIGNALSCOPE_",
        extra="ignore",
        case_sensitive=False,
    )

    environment: Literal["development", "test", "staging", "production"] = "development"
    log_level: str = "INFO"
    data_dir: Path = Field(default=Path("data/demo"))
    cors_origins: str = "http://localhost:3000"

    llm_provider: Literal["deterministic", "openai"] = "deterministic"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"

    postgres_dsn: str | None = None
    qdrant_url: str | None = None
    qdrant_api_key: str | None = None
    otel_endpoint: str | None = None

    max_recommendations: int = Field(default=5, ge=1, le=10)
    retrieval_candidate_limit: int = Field(default=12, ge=3, le=50)
    minimum_evidence_coverage: float = Field(default=0.8, ge=0.0, le=1.0)

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached immutable settings object."""

    return Settings()
