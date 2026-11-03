from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _clean_optional(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    value = " ".join(value.split())
    return value or None


class ProductInput(BaseModel):
    """Normalized product data supplied by a content manager."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, description="Product name")
    manufacturer: str | None = None
    specs: dict[str, str] = Field(default_factory=dict)
    description: str | None = None

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: Any) -> str:
        cleaned = _clean_optional(value)
        if not cleaned:
            raise ValueError("Название товара не может быть пустым")
        return cleaned

    @field_validator("manufacturer", "description", mode="before")
    @classmethod
    def clean_optional_fields(cls, value: Any) -> str | None:
        return _clean_optional(value)

    @field_validator("specs", mode="before")
    @classmethod
    def clean_specs(cls, value: Any) -> dict[str, str]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ValueError("Поле specs должно быть объектом")

        result: dict[str, str] = {}
        for raw_key, raw_value in value.items():
            key = _clean_optional(raw_key)
            if not key:
                continue
            if raw_value is None:
                continue
            cleaned_value = _clean_optional(raw_value)
            if cleaned_value:
                result[key] = cleaned_value
        return result
