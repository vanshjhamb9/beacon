"""Evidence chain — exactly why Beacon trusts a company."""

from __future__ import annotations

from typing import Any


EVIDENCE_KINDS = (
    "yc_page",
    "founder_page",
    "company_website",
    "hiring_page",
    "crunchbase",
    "github",
    "news",
    "hunter",
    "apollo",
    "linkedin",
    "product_hunt",
    "sec_filing",
    "rss",
    "internal",
)


def normalize_evidence_kind(raw: str | None) -> str:
    value = (raw or "internal").strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "website": "company_website",
        "domain": "company_website",
        "founder": "founder_page",
        "yc": "yc_page",
        "ycombinator": "yc_page",
        "hiring": "hiring_page",
        "jobs": "hiring_page",
    }
    return aliases.get(value, value)


def serialize_evidence(item: dict[str, Any]) -> dict[str, Any]:
    kind = normalize_evidence_kind(str(item.get("kind") or item.get("source") or "internal"))
    return {
        "id": str(item.get("id") or ""),
        "kind": kind,
        "label": item.get("label") or kind.replace("_", " ").title(),
        "url": item.get("url"),
        "snippet": item.get("snippet") or item.get("detail") or "",
        "provider": item.get("provider") or kind,
        "confidence": float(item.get("confidence") or 0),
        "occurred_at": item.get("occurred_at"),
        "payload": item.get("payload") or {},
    }


def assemble_evidence_chain(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for raw in items:
        row = serialize_evidence(raw)
        key = f"{row['kind']}|{row.get('url') or ''}|{row['label']}"
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out
