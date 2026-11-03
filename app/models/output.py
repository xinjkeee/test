from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Characteristic(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1)
    value: str = Field(..., min_length=1)
    source: Literal["input", "missing"]


class CommercialBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_audience: str = Field(..., min_length=1)
    solves_tasks: list[str] = Field(default_factory=list, min_length=1)

    @field_validator("solves_tasks")
    @classmethod
    def clean_tasks(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item and item.strip()]


class ProductDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    seo_title: str = Field(..., min_length=1)
    seo_description: str = Field(..., min_length=1)
    characteristics: list[Characteristic] = Field(default_factory=list)
    search_queries: list[str] = Field(..., min_length=3, max_length=5)
    commercial_block: CommercialBlock
    missing_data: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @field_validator("search_queries")
    @classmethod
    def clean_queries(cls, value: list[str]) -> list[str]:
        cleaned = []
        for query in value:
            query = query.strip()
            if query and query not in cleaned:
                cleaned.append(query)
        return cleaned
