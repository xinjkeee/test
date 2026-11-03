from __future__ import annotations

import logging

from pydantic import ValidationError

from app.config import Settings
from app.models.input import ProductInput
from app.models.output import ProductDraft
from app.services.llm_client import LLMClient, LLMError
from app.services.prompt_builder import SYSTEM_PROMPT, build_user_prompt
from app.services.validator import DraftValidationError, validate_draft

logger = logging.getLogger(__name__)


class GenerationError(RuntimeError):
    """An error safe to show to an API consumer."""


class ProductGenerator:
    def __init__(self, settings: Settings, llm_client: LLMClient | None = None) -> None:
        self.settings = settings
        self.llm_client = llm_client or LLMClient(settings)

    async def generate(self, product: ProductInput) -> ProductDraft:
        repair_message: str | None = None
        attempts = self.settings.llm_max_retries + 1
        last_error: Exception | None = None

        for attempt in range(attempts):
            try:
                raw = await self.llm_client.complete_json(
                    SYSTEM_PROMPT,
                    build_user_prompt(product, repair_message),
                )
                draft = ProductDraft.model_validate(raw)
                return validate_draft(draft, product)
            except (LLMError, ValidationError, DraftValidationError) as exc:
                last_error = exc
                if isinstance(exc, LLMError) and not exc.retryable:
                    break
                if attempt + 1 >= attempts:
                    break
                repair_message = str(exc)
                logger.info("Retrying LLM generation after validation error")

        if isinstance(last_error, LLMError):
            raise GenerationError(str(last_error)) from last_error
        if isinstance(last_error, DraftValidationError):
            raise GenerationError(
                "LLM вернула результат, который не прошёл проверку: "
                + "; ".join(last_error.problems)
            ) from last_error
        raise GenerationError(
            "LLM вернула результат, не соответствующий требуемой схеме."
        ) from last_error
