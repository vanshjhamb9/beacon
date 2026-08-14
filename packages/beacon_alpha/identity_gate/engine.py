from __future__ import annotations

from typing import Any

from beacon_alpha.models.types import AttributedValue, IdentityGateResult, UNKNOWN

REQUIRED = (
    "identity",
    "website",
    "business_description",
    "industry",
    "country",
    "evidence",
    "opportunity",
    "source",
)


class IdentityGateEngine:
    """Rule 2 — required fields before entering Beacon; otherwise reject."""

    def evaluate(self, payload: dict[str, Any]) -> IdentityGateResult:
        collected_at = payload.get("collected_at") or payload.get("last_seen_at")
        source = str(payload.get("source") or "company_record")

        values = {
            "identity": payload.get("company_name") or payload.get("legal_name") or payload.get("name"),
            "website": payload.get("website") or payload.get("primary_domain") or payload.get("domain"),
            "business_description": payload.get("business_description")
            or payload.get("description")
            or payload.get("narrative")
            or payload.get("memory_summary"),
            "industry": payload.get("industry"),
            "country": payload.get("country") or payload.get("hq") or payload.get("location"),
            "evidence": payload.get("evidence") or payload.get("timeline") or payload.get("evidence_ids"),
            "opportunity": payload.get("opportunity")
            or payload.get("use_case")
            or payload.get("recommended_service")
            or payload.get("buying_intent")
            or (payload.get("signals") or [None])[0],
            "source": payload.get("source"),
        }

        fields: dict[str, AttributedValue] = {}
        missing: list[str] = []
        evidence: list[str] = []

        for key in REQUIRED:
            val = values.get(key)
            present = bool(val) and val != UNKNOWN
            if key == "evidence":
                present = bool(val)
            if key == "business_description":
                present = bool(val) and len(str(val).strip()) >= 20
            if key == "opportunity" and isinstance(val, dict):
                present = bool(val.get("summary") or val.get("signal") or val.get("value"))
                val = val.get("summary") or val.get("signal") or val.get("value")
            if present:
                fields[key] = AttributedValue.of(
                    f"{len(val)} items" if key == "evidence" and not isinstance(val, str) else val,
                    source=source,
                    collected_at=collected_at,
                    confidence=90.0 if key != "opportunity" else 75.0,
                    evidence=[f"{key}_observed"],
                )
                evidence.append(f"has_{key}")
            else:
                missing.append(key)
                fields[key] = AttributedValue.unknown(reason=f"missing_{key}")

        return IdentityGateResult(
            passed=len(missing) == 0,
            missing=missing,
            fields=fields,
            evidence=evidence + [f"passed:{len(missing) == 0}"],
        )
