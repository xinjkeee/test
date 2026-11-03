from __future__ import annotations

import pytest

from app.models.input import ProductInput
from app.models.output import Characteristic, ProductDraft
from app.services.validator import DraftValidationError, validate_draft


def product() -> ProductInput:
    return ProductInput.model_validate(
        {
            "name": "Манометр показывающий DM 02",
            "manufacturer": "Манотомь",
            "specs": {"диапазон измерений": "0–1,6 МПа", "класс точности": "1,5"},
            "description": "Прибор предназначен для измерения избыточного давления.",
        }
    )


def valid_draft() -> ProductDraft:
    return ProductDraft.model_validate(
        {
            "seo_title": "Манометр DM 02 Манотомь 0–1,6 МПа",
            "seo_description": "Описание товара. " * 50,
            "characteristics": [
                {"name": "диапазон измерений", "value": "0–1,6 МПа", "source": "input"},
                {"name": "класс точности", "value": "1,5", "source": "input"},
            ],
            "search_queries": ["манометр DM 02", "манометр 0–1,6 МПа", "Манотомь манометр"],
            "commercial_block": {
                "target_audience": "Специалисты, которым требуется измерять давление.",
                "solves_tasks": ["измерение избыточного давления"],
            },
            "missing_data": [],
        }
    )


def test_validator_rebuilds_characteristics_from_input() -> None:
    result = validate_draft(valid_draft(), product())
    assert [item.value for item in result.characteristics] == ["0–1,6 МПа", "1,5"]


def test_validator_rejects_unknown_characteristic() -> None:
    draft = valid_draft()
    draft.characteristics.append(
        Characteristic(name="степень защиты", value="IP65", source="input")
    )
    with pytest.raises(DraftValidationError, match="неизвестная характеристика"):
        validate_draft(draft, product())


def test_validator_rejects_invented_number() -> None:
    draft = valid_draft().model_copy(update={"seo_description": "Работает при 220 В. " * 100})
    with pytest.raises(DraftValidationError, match="числовые значения"):
        validate_draft(draft, product())


def test_missing_marker_is_not_treated_as_confirmed_fact() -> None:
    incomplete = ProductInput.model_validate(
        {"name": "Датчик", "specs": {"выходной сигнал": "не указан"}}
    )
    draft = ProductDraft.model_validate(
        {
            "seo_title": "Датчик давления",
            "seo_description": "Описание прибора. " * 50,
            "characteristics": [
                Characteristic(
                    name="выходной сигнал",
                    value="данных нет",
                    source="missing",
                )
            ],
            "search_queries": [
                "датчик давления",
                "датчик контроля давления",
                "промышленный датчик",
            ],
            "commercial_block": {
                "target_audience": "Специалисты, которым требуется контроль давления.",
                "solves_tasks": ["контроль давления"],
            },
            "missing_data": [],
        }
    )
    result = validate_draft(draft, incomplete)
    assert result.characteristics[0].value == "данных нет"
    assert result.characteristics[0].source == "missing"
