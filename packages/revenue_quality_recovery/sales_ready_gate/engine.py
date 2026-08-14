from __future__ import annotations

from typing import Any

from revenue_quality_recovery.models.types import (
    RevenueVerdict,
    SalesReadyGateResult,
    SalesReadyRequirement,
    UNKNOWN,
)

REQUIRED_FIELDS = (
    "real_company_name",
    "website",
    "domain",
    "linkedin_company",
    "industry",
    "country",
    "employee_estimate",
    "ai_service_match",
    "buying_intent",
    "collection_evidence",
)


class SalesReadyGateEngine:
    """Rule 1 — every company is REJECTED or SALES READY. No middle state."""

    def evaluate(self, payload: dict[str, Any]) -> SalesReadyGateResult:
        collected_at = payload.get("collected_at") or payload.get("last_seen_at")
        values = {
            "real_company_name": payload.get("company_name") or payload.get("legal_name") or payload.get("name"),
            "website": payload.get("website") or payload.get("primary_domain"),
            "domain": payload.get("domain") or payload.get("canonical_domain"),
            "linkedin_company": payload.get("linkedin_company")
            or payload.get("linkedin_company_url")
            or payload.get("linkedin_url"),
            "industry": payload.get("industry"),
            "country": payload.get("country") or payload.get("hq") or payload.get("location"),
            "employee_estimate": payload.get("employee_estimate") or payload.get("employees"),
            "ai_service_match": payload.get("ai_service_match")
            or payload.get("recommended_service")
            or self._first_service(payload),
            "buying_intent": payload.get("buying_intent")
            or payload.get("intent_level")
            or self._intent_present(payload),
            "collection_evidence": self._evidence_present(payload),
        }
        # Derive domain from website if needed
        if not values["domain"] and values["website"]:
            values["domain"] = str(values["website"]).lower().removeprefix("https://").removeprefix("http://").removeprefix("www.").split("/")[0]

        requirements: list[SalesReadyRequirement] = []
        missing: list[str] = []
        evidence: list[str] = []

        for field in REQUIRED_FIELDS:
            val = values.get(field)
            present = val not in (None, "", UNKNOWN, False, [])
            if field == "buying_intent" and isinstance(val, (int, float)):
                present = float(val) > 0
            if field == "collection_evidence":
                present = bool(val)
            requirements.append(
                SalesReadyRequirement(
                    field=field,
                    present=present,
                    value=val if present else UNKNOWN,
                    evidence=[f"{field}_observed"] if present else [f"missing_{field}"],
                )
            )
            if present:
                evidence.append(f"has_{field}")
            else:
                missing.append(field)

        complete = len(missing) == 0
        verdict = RevenueVerdict.SALES_READY if complete else RevenueVerdict.REJECTED
        confidence = round(100.0 * (len(REQUIRED_FIELDS) - len(missing)) / len(REQUIRED_FIELDS), 2)
        return SalesReadyGateResult(
            verdict=verdict,
            requirements=requirements,
            missing=missing,
            complete=complete,
            confidence=confidence,
            evidence=evidence + [f"verdict:{verdict.value}", f"collected_at:{collected_at or UNKNOWN}"],
        )

    def _first_service(self, payload: dict[str, Any]) -> Any:
        services = payload.get("recommended_services") or payload.get("services") or []
        if services and isinstance(services[0], dict):
            return services[0].get("recommended_service") or services[0].get("service")
        if services:
            return services[0]
        return None

    def _intent_present(self, payload: dict[str, Any]) -> Any:
        if payload.get("intent_score"):
            return payload.get("intent_score")
        signals = payload.get("signals") or payload.get("intent_signals") or []
        if signals:
            return signals[0] if not isinstance(signals[0], dict) else signals[0].get("signal") or signals[0].get("value")
        return None

    def _evidence_present(self, payload: dict[str, Any]) -> bool:
        return bool(payload.get("evidence") or payload.get("evidence_ids") or payload.get("timeline") or payload.get("collection_evidence"))
