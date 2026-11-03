from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from app.config import get_settings
from app.models.input import ProductInput
from app.services.generator import GenerationError, ProductGenerator
from app.services.markdown import draft_to_markdown


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a B2B product card draft")
    parser.add_argument("input", type=Path, help="Path to product JSON")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    return parser.parse_args()


async def run() -> int:
    args = parse_args()
    try:
        product = ProductInput.model_validate_json(args.input.read_text(encoding="utf-8"))
        draft = await ProductGenerator(get_settings()).generate(product)
    except (OSError, json.JSONDecodeError, ValidationError, GenerationError) as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1

    if args.format == "markdown":
        print(draft_to_markdown(draft), end="")
    else:
        print(json.dumps(draft.model_dump(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
