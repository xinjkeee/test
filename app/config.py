from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    llm_api_key: str | None
    llm_model: str
    llm_base_url: str
    llm_timeout_seconds: float
    llm_max_retries: int
    log_level: str

    @classmethod
    def from_env(cls) -> Settings:
        load_dotenv()
        timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
        retries = int(os.getenv("LLM_MAX_RETRIES", "1"))
        if timeout <= 0:
            raise ValueError("LLM_TIMEOUT_SECONDS must be greater than zero")
        if retries < 0:
            raise ValueError("LLM_MAX_RETRIES cannot be negative")
        return cls(
            llm_api_key=os.getenv("LLM_API_KEY"),
            llm_model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            llm_base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
            llm_timeout_seconds=timeout,
            llm_max_retries=retries,
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
