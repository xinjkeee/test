from __future__ import annotations

from dataclasses import dataclass

from app.models.input import ProductInput
from app.models.output import Characteristic, ProductDraft
from app.utils.text import all_text, extract_numbers, is_missing_marker, normalize_text


class DraftValidationError(ValueError):
    """Raised when an LLM draft violates business rules."""

    def __init__(self, problems: list[str]) -> None:
        self.problems = problems
        super().__init__("; ".join(problems))


@dataclass(frozen=True)
class ValidationResult:
    draft: ProductDraft
    problems: list[str]


def _computed_missing_data(product: ProductInput) -> list[str]:
    missing: list[str] = []
    if not product.manufacturer:
        missing.append("производитель")
    if not product.description:
        missing.append("описание и назначение")
    if not product.specs:
        missing.append("технические характеристики")
    return missing


def _canonical_characteristics(product: ProductInput) -> list[Characteristic]:
    return [
        Characteristic(
            name=name,
            value="данных нет" if is_missing_marker(value) else value,
            source="missing" if is_missing_marker(value) else "input",
        )
        for name, value in product.specs.items()
    ]


def validate_draft(draft: ProductDraft, product: ProductInput) -> ProductDraft:
    # Pydantic models can still be mutated after construction; revalidate at the
    # business boundary before inspecting nested values.
    draft = ProductDraft.model_validate(draft.model_dump())
    problems: list[str] = []
    if len(draft.seo_title) > 70:
        problems.append(f"seo_title длиннее 70 символов: {len(draft.seo_title)}")
    description_length = len(draft.seo_description)
    if not 800 <= description_length <= 1200:
        problems.append(
            f"seo_description должен содержать 800–1200 символов, сейчас {description_length}"
        )
    if not 3 <= len(draft.search_queries) <= 5:
        problems.append("search_queries должен содержать от 3 до 5 уникальных запросов")

    input_by_name = {normalize_text(name): (name, value) for name, value in product.specs.items()}
    for characteristic in draft.characteristics:
        key = normalize_text(characteristic.name)
        if key not in input_by_name:
            problems.append(f"неизвестная характеристика: {characteristic.name}")
            continue
        original_name, original_value = input_by_name[key]
        original_is_missing = is_missing_marker(original_value)
        expected_source = "missing" if original_is_missing else "input"
        if characteristic.source != expected_source:
            problems.append(f"характеристика {original_name} имеет неверный source")
        if original_is_missing:
            if not is_missing_marker(characteristic.value):
                problems.append(
                    f"характеристика {original_name} должна быть помечена как «данных нет»"
                )
        elif normalize_text(characteristic.value) != normalize_text(original_value):
            problems.append(f"значение характеристики {original_name} изменено или выдумано")

    returned_keys = {normalize_text(item.name) for item in draft.characteristics}
    for name in product.specs:
        if normalize_text(name) not in returned_keys:
            problems.append(f"характеристика отсутствует в ответе: {name}")

    input_numbers = extract_numbers(
        all_text(
            [
                product.name,
                product.manufacturer or "",
                product.description or "",
                *product.specs.values(),
            ]
        )
    )
    generated_text = all_text(
        [
            draft.seo_title,
            draft.seo_description,
            *draft.search_queries,
            draft.commercial_block.target_audience,
            *draft.commercial_block.solves_tasks,
            *(item.value for item in draft.characteristics),
        ]
    )
    invented_numbers = extract_numbers(generated_text) - input_numbers
    if invented_numbers:
        problems.append(
            "в тексте обнаружены числовые значения, отсутствующие во входных данных: "
            + ", ".join(sorted(invented_numbers))
        )

    computed_missing = _computed_missing_data(product)
    merged_missing: list[str] = []
    marker_missing = [
        name for name, value in product.specs.items() if is_missing_marker(value)
    ]
    for item in [*computed_missing, *marker_missing, *draft.missing_data]:
        item = item.strip()
        if item and item not in merged_missing:
            merged_missing.append(item)

    # Rebuild this section from trusted input so a model cannot alter technical values.
    safe_draft = draft.model_copy(
        update={
            "characteristics": _canonical_characteristics(product),
            "missing_data": merged_missing,
        }
    )
    if problems:
        raise DraftValidationError(problems)
    return safe_draft
