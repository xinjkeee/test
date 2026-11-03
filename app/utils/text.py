from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

MISSING_MARKERS = {
    "данных нет",
    "нет данных",
    "не указано",
    "не указана",
    "не указан",
    "не указаны",
    "отсутствует",
    "отсутствуют",
}


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).strip().casefold()
    value = value.replace("ё", "е")
    value = re.sub(r"\s+", " ", value)
    return value


def is_missing_marker(value: str) -> bool:
    normalized = normalize_text(value).strip(" .;:–—-")
    return normalized in MISSING_MARKERS


def extract_numbers(value: str) -> set[str]:
    """Return normalized numeric tokens for a conservative fact check."""
    pattern = r"(?<![A-Za-zА-Яа-я])\d+(?:[.,]\d+)?"
    return {token.replace(",", ".") for token in re.findall(pattern, value)}


def all_text(values: Iterable[str]) -> str:
    return " ".join(value for value in values if value)
