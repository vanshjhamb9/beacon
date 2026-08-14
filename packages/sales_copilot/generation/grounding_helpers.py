from __future__ import annotations

from typing import Any

from sales_copilot.models.types import INSUFFICIENT, EvidenceItem, SectionAttribution


def evidence_or_insufficient(values: list[str] | list[dict[str, str]] | str | None) -> str:
    if values is None:
        return INSUFFICIENT
    if isinstance(values, str):
        return values.strip() or INSUFFICIENT
    if not values:
        return INSUFFICIENT
    lines: list[str] = []
    for value in values:
        if isinstance(value, dict):
            name = (value.get("name") or "").strip()
            role = (value.get("role") or "").strip()
            text = f"{name} ({role})" if name and role else name or role
        else:
            text = str(value).strip()
        if text:
            lines.append(f"- {text}")
    return "\n".join(lines) if lines else INSUFFICIENT


def attribution_for(
    section: str,
    facts: dict[str, Any],
    *,
    categories: tuple[str, ...] | None = None,
    grounded: bool | None = None,
) -> SectionAttribution:
    evidence: list[EvidenceItem] = list(facts.get("evidence") or [])
    if categories:
        evidence = [item for item in evidence if item.category in categories]
    summaries = [item.summary for item in evidence[:8]]
    ids = [item.reference_id or f"{item.category}:{idx}" for idx, item in enumerate(evidence[:8])]
    is_grounded = grounded if grounded is not None else bool(summaries)
    return SectionAttribution(
        section=section,
        evidence_ids=ids,
        evidence_summaries=summaries,
        grounded=is_grounded,
        note="" if is_grounded else INSUFFICIENT,
    )


def join_sentences(*parts: str) -> str:
    cleaned = [part.strip() for part in parts if part and part.strip() and part.strip() != INSUFFICIENT]
    if not cleaned:
        return INSUFFICIENT
    return " ".join(cleaned)
