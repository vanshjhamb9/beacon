"""Enrichment attempt history — succeeded / failed / skipped."""

from __future__ import annotations

from typing import Any


def serialize_enrichment(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row.get("id") or ""),
        "provider": row.get("provider") or "internal",
        "enrichment_type": row.get("enrichment_type") or row.get("kind") or "enrichment",
        "status": row.get("status") or ("success" if row.get("success") else "failed"),
        "success": bool(row.get("success")),
        "fields_added": list(row.get("fields_added") or []),
        "error": row.get("error") or row.get("detail") or "",
        "latency_ms": row.get("latency_ms"),
        "occurred_at": row.get("occurred_at"),
        "payload": row.get("payload") or {},
    }


def summarize_enrichments(rows: list[dict[str, Any]]) -> dict[str, Any]:
    items = [serialize_enrichment(r) for r in rows]
    succeeded = [i for i in items if i["success"] or i["status"] == "success"]
    failed = [i for i in items if not i["success"] and i["status"] not in {"waiting", "disabled", "coming_soon", "reserved"}]
    pending = [i for i in items if i["status"] in {"waiting", "pending"}]
    return {
        "attempted": len(items),
        "succeeded": len(succeeded),
        "failed": len(failed),
        "pending": len(pending),
        "items": items,
        "succeeded_providers": sorted({i["provider"] for i in succeeded}),
        "failed_providers": sorted({i["provider"] for i in failed}),
    }
