from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse

from app.config import Settings, get_settings
from app.models.input import ProductInput
from app.models.output import ProductDraft
from app.services.generator import GenerationError, ProductGenerator
from app.services.markdown import draft_to_markdown

router = APIRouter(prefix="/api/v1", tags=["generation"])


def get_generator(
    settings: Annotated[Settings, Depends(get_settings)],
) -> ProductGenerator:
    return ProductGenerator(settings)


async def _generate(product: ProductInput, generator: ProductGenerator) -> ProductDraft:
    try:
        return await generator.generate(product)
    except GenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "generation_failed", "message": str(exc)},
        ) from exc


@router.post("/generate", response_model=ProductDraft, summary="Generate a product draft")
async def generate(
    product: ProductInput,
    generator: Annotated[ProductGenerator, Depends(get_generator)],
) -> ProductDraft:
    return await _generate(product, generator)


@router.post(
    "/generate/markdown",
    response_class=PlainTextResponse,
    summary="Generate a product draft as Markdown",
)
async def generate_markdown(
    product: ProductInput,
    generator: Annotated[ProductGenerator, Depends(get_generator)],
) -> PlainTextResponse:
    draft = await _generate(product, generator)
    return PlainTextResponse(draft_to_markdown(draft), media_type="text/markdown; charset=utf-8")
