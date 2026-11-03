from __future__ import annotations

import pytest

from app.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(
        llm_api_key="test-key",
        llm_model="test-model",
        llm_base_url="https://example.test/v1",
        llm_timeout_seconds=5,
        llm_max_retries=1,
        log_level="INFO",
    )
