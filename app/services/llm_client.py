from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)


class LLMError(RuntimeError):
    """An expected failure while calling or parsing the LLM response."""

    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


class LLMClient:
    def __init__(
        self,
        settings: Settings,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.settings = settings
        self.transport = transport

    async def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        if not self.settings.llm_api_key:
            raise LLMError(
                "LLM_API_KEY не задан. Укажите ключ в .env или переменных окружения.",
            )

        payload = {
            "model": self.settings.llm_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.settings.llm_api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.settings.llm_timeout_seconds,
                transport=self.transport,
            ) as client:
                response = await client.post(
                    f"{self.settings.llm_base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
        except httpx.TimeoutException as exc:
            raise LLMError("Превышено время ожидания ответа LLM.", retryable=True) from exc
        except httpx.HTTPError as exc:
            raise LLMError("Не удалось подключиться к LLM API.", retryable=True) from exc

        if response.status_code >= 500:
            raise LLMError("LLM API временно недоступен.", retryable=True)
        if response.status_code >= 400:
            logger.warning("LLM API returned status %s", response.status_code)
            raise LLMError("LLM API отклонил запрос.", retryable=False)

        try:
            body = response.json()
            content = body["choices"][0]["message"]["content"]
            if isinstance(content, list):
                content = "".join(
                    part.get("text", "") for part in content if isinstance(part, dict)
                )
            if not isinstance(content, str) or not content.strip():
                raise ValueError("empty content")
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                raise ValueError("response root is not an object")
            return parsed
        except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise LLMError(
                "LLM вернула ответ в некорректном JSON-формате.",
                retryable=True,
            ) from exc
