"""Lead explainer — promotion reasons and field provenance summaries."""

from __future__ import annotations

from typing import Any


def promotion_explanation(facts: dict[str, Any]) -> dict[str, Any]:
    checklist = [
        ("decision_maker", bool(facts.get("has_founder") or facts.get("founder") or facts.get("decision_maker_at"))),
        ("business_email", bool(facts.get("has_email") or facts.get("business_email") or facts.get("email_at"))),
        ("confidence", float(facts.get("confidence") or 0) >= 90),
        ("trust", float(facts.get("trust") or 0) >= 95),
        ("website", bool(facts.get("has_website") or facts.get("domain") or facts.get("website_at"))),
    ]
    passed = [name for name, ok in checklist if ok]
    missing = [name for name, ok in checklist if not ok]
    revenue_ready = bool(facts.get("revenue_ready"))
    return {
        "promoted": revenue_ready,
        "reason": (
            "Revenue Ready — decision maker, business email, confidence, and trust thresholds met"
            if revenue_ready and not missing
            else (
                "Partially ready — missing: " + ", ".join(missing)
                if missing
                else "Not promoted"
            )
        ),
        "passed": passed,
        "missing": missing,
        "confidence": float(facts.get("confidence") or 0),
        "trust": float(facts.get("trust") or 0),
    }


def serialize_field_history(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                "id": str(row.get("id") or ""),
                "field_name": row.get("field_name") or row.get("field") or "",
                "field_value": row.get("field_value") or row.get("value"),
                "provider": row.get("provider") or "internal",
                "confidence": float(row.get("confidence") or 0),
                "occurred_at": row.get("occurred_at"),
                "source_url": row.get("source_url"),
                "evidence_id": row.get("evidence_id"),
                "payload": row.get("payload") or {},
            }
        )
    # Latest value per field first, keep full history ordered
    return sorted(out, key=lambda r: (r["field_name"], r.get("occurred_at") or ""))


def latest_fields(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in serialize_field_history(rows):
        latest[row["field_name"]] = row
    return latest


def lead_summary_dict(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "company": payload.get("company") or payload.get("company_name") or "",
        "domain": payload.get("domain") or payload.get("primary_domain"),
        "current_stage": payload.get("current_stage") or "unknown",
        "current_score": float(payload.get("current_score") or payload.get("score") or 0),
        "confidence": float(payload.get("confidence") or 0),
        "trust": float(payload.get("trust") or 0),
        "revenue_ready": bool(payload.get("revenue_ready")),
        "pipeline_value": float(payload.get("pipeline_value") or 0),
        "source": payload.get("source") or payload.get("connector") or "unknown",
        "created_at": payload.get("created_at"),
        "last_updated": payload.get("last_updated") or payload.get("updated_at"),
        "company_id": payload.get("company_id"),
        "lead_id": payload.get("lead_id") or payload.get("company_id"),
        "revenue_ready_id": payload.get("revenue_ready_id"),
        "industry": payload.get("industry"),
        "founder": payload.get("founder"),
        "business_email": payload.get("business_email"),
    }
