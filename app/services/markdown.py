from __future__ import annotations

from app.models.output import ProductDraft


def draft_to_markdown(draft: ProductDraft) -> str:
    lines = [
        f"# {draft.seo_title}",
        "",
        "## SEO-описание",
        "",
        draft.seo_description,
        "",
        "## Характеристики",
        "",
    ]
    if draft.characteristics:
        lines.extend(
            f"- **{item.name}:** {item.value}" for item in draft.characteristics
        )
    else:
        lines.append("- Данных нет")

    lines.extend(["", "## Поисковые запросы", ""])
    lines.extend(f"- {query}" for query in draft.search_queries)
    lines.extend(
        [
            "",
            "## Для менеджера",
            "",
            f"**Кому подходит:** {draft.commercial_block.target_audience}",
            "",
            "**Какие задачи решает:**",
        ]
    )
    lines.extend(f"- {task}" for task in draft.commercial_block.solves_tasks)
    lines.extend(["", "## Требует уточнения", ""])
    if draft.missing_data:
        lines.extend(f"- {item}" for item in draft.missing_data)
    else:
        lines.append("- Нет")
    if draft.warnings:
        lines.extend(["", "## Предупреждения", ""])
        lines.extend(f"- {warning}" for warning in draft.warnings)
    return "\n".join(lines) + "\n"
