from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.models.input import ProductInput


def test_product_input_normalizes_optional_fields() -> None:
    product = ProductInput.model_validate(
        {
            "name": "  Манометр   DM 02 ",
            "manufacturer": "  Манотомь ",
            "specs": {" диапазон ": " 0–1,6 МПа ", "пустое": "  "},
            "description": "  Описание прибора ",
        }
    )
    assert product.name == "Манометр DM 02"
    assert product.manufacturer == "Манотомь"
    assert product.specs == {"диапазон": "0–1,6 МПа"}


def test_empty_name_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ProductInput.model_validate({"name": "  "})


def test_missing_specs_are_allowed() -> None:
    product = ProductInput.model_validate({"name": "Датчик"})
    assert product.specs == {}
