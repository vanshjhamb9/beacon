"""Provider history cards — reserved slots for future enrichment hubs."""

from __future__ import annotations

from typing import Any

from lead_intelligence import PROVIDER_CATALOG


DEFAULT_PROVIDER_STATUS: dict[str, str] = {
    "hunter": "available",
    "apollo": "coming_soon",
    "linkedin": "waiting",
    "people_data_labs": "disabled",
    "clearbit": "coming_soon",
    "crunchbase": "coming_soon",
    "builtwith": "coming_soon",
    "wappalyzer": "coming_soon",
    "google_maps": "coming_soon",
    "meta": "coming_soon",
    "opencorporates": "coming_soon",
}


def empty_provider_card(name: str) -> dict[str, Any]:
    status = DEFAULT_PROVIDER_STATUS.get(name, "reserved")
    return {
        "provider": name,
        "label": name.replace("_", " ").title(),
        "status": status,
        "latency_ms": None,
        "fields_added": [],
        "credits_used": None,
        "success": None,
        "confidence": None,
        "attempts": 0,
        "last_run_at": None,
        "detail": status.replace("_", " ").title(),
        "payload": {},
    }


def merge_provider_history(
    rows: list[dict[str, Any]],
    *,
    include_reserved: bool = True,
) -> list[dict[str, Any]]:
    by_name: dict[str, dict[str, Any]] = {}
    for name in PROVIDER_CATALOG:
        if include_reserved or name in DEFAULT_PROVIDER_STATUS:
            by_name[name] = empty_provider_card(name)

    for row in rows:
        name = str(row.get("provider") or "").strip().lower().replace(" ", "_")
        if not name:
            continue
        base = by_name.get(name) or empty_provider_card(name)
        fields = list(base.get("fields_added") or [])
        for field in row.get("fields_added") or []:
            if field not in fields:
                fields.append(field)
        success = row.get("success")
        attempts = int(base.get("attempts") or 0) + 1
        base.update(
            {
                "provider": name,
                "label": name.replace("_", " ").title(),
                "status": row.get("status") or ("success" if success else "failed"),
                "latency_ms": row.get("latency_ms"),
                "fields_added": fields,
                "credits_used": row.get("credits_used"),
                "success": success,
                "confidence": row.get("confidence"),
                "attempts": attempts,
                "last_run_at": row.get("occurred_at") or row.get("last_run_at") or base.get("last_run_at"),
                "detail": row.get("detail") or base.get("detail") or "",
                "payload": row.get("payload") or base.get("payload") or {},
            }
        )
        by_name[name] = base

    # Prefer catalog order, then any extras
    ordered = [by_name[n] for n in PROVIDER_CATALOG if n in by_name]
    extras = [v for k, v in by_name.items() if k not in PROVIDER_CATALOG]
    return ordered + extras


def connector_contribution(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate provider contribution metrics."""
    buckets: dict[str, dict[str, Any]] = {}
    for row in rows:
        name = str(row.get("provider") or "unknown").lower()
        b = buckets.setdefault(
            name,
            {
                "provider": name,
                "label": name.replace("_", " ").title(),
                "companies_affected": 0,
                "emails_added": 0,
                "dm_added": 0,
                "revenue_ready_created": 0,
                "successes": 0,
                "attempts": 0,
                "success_pct": 0.0,
                "status": row.get("status") or "active",
            },
        )
        b["attempts"] += 1
        if row.get("success"):
            b["successes"] += 1
        fields = set(row.get("fields_added") or [])
        if "email" in fields or "business_email" in fields:
            b["emails_added"] += 1
        if "decision_maker" in fields or "founder" in fields:
            b["dm_added"] += 1
        if row.get("revenue_ready"):
            b["revenue_ready_created"] += 1
        company_id = row.get("company_id")
        if company_id:
            seen = b.setdefault("_companies", set())
            if isinstance(seen, set):
                seen.add(str(company_id))

    out: list[dict[str, Any]] = []
    for b in buckets.values():
        companies = b.pop("_companies", set())
        b["companies_affected"] = len(companies) if isinstance(companies, set) else int(b.get("companies_affected") or 0)
        attempts = max(int(b["attempts"]), 1)
        b["success_pct"] = round(100.0 * int(b["successes"]) / attempts, 1)
        out.append(b)
    return sorted(out, key=lambda r: (-r["revenue_ready_created"], -r["companies_affected"], r["provider"]))
