from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from production_hardening.models.types import LeadQualityScore

HIDE_THRESHOLD = 70.0


class LeadQualityScorer:
    """PH-1 lead quality score (max 100). Hide below 70."""

    WEIGHTS = {
        "business_identity": 15.0,
        "verified_website": 15.0,
        "intent_signals": 20.0,
        "decision_maker": 15.0,
        "verified_email": 15.0,
        "verified_phone": 10.0,
        "freshness": 5.0,
        "technology_match": 5.0,
        "buying_signals": 10.0,
    }

    def score(self, payload: dict[str, Any]) -> LeadQualityScore:
        identity = 15.0 if payload.get("business_identity") or (payload.get("company_name") and payload.get("domain")) else 0.0
        website = 15.0 if payload.get("verified_website") or payload.get("primary_domain") or payload.get("website") else 0.0
        intent = min(20.0, float(payload.get("intent_score") or 0.0))
        if payload.get("intent_signals") and intent == 0:
            intent = min(20.0, 5.0 * len(payload.get("intent_signals") or []))
        dm = 15.0 if payload.get("decision_maker") or payload.get("has_decision_maker") else 0.0
        email = 15.0 if payload.get("verified_email") or payload.get("emails") else 0.0
        phone = 10.0 if payload.get("verified_phone") or payload.get("phones") else 0.0
        freshness = self._freshness(payload.get("collected_at") or payload.get("last_seen_at") or payload.get("freshness_hours"))
        tech = 5.0 if payload.get("technology_match") or payload.get("technologies") else 0.0
        buying = min(10.0, float(payload.get("buying_signal_score") or 0.0))
        if payload.get("buying_signals") and buying == 0:
            buying = min(10.0, 2.5 * len(payload.get("buying_signals") or []))

        total = round(identity + website + intent + dm + email + phone + freshness + tech + buying, 2)
        evidence = [
            f"identity:{identity}",
            f"website:{website}",
            f"intent:{intent}",
            f"decision_maker:{dm}",
            f"email:{email}",
            f"phone:{phone}",
            f"freshness:{freshness}",
            f"tech:{tech}",
            f"buying:{buying}",
            f"total:{total}",
        ]
        return LeadQualityScore(
            total=total,
            business_identity=identity,
            verified_website=website,
            intent_signals=intent,
            decision_maker=dm,
            verified_email=email,
            verified_phone=phone,
            freshness=freshness,
            technology_match=tech,
            buying_signals=buying,
            visible=total >= HIDE_THRESHOLD,
            evidence=evidence,
        )

    def _freshness(self, value: Any) -> float:
        if value is None:
            return 0.0
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            hours = float(value)
        else:
            try:
                dt = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=UTC)
                hours = (datetime.now(UTC) - dt.astimezone(UTC)).total_seconds() / 3600.0
            except Exception:  # noqa: BLE001
                return 0.0
        if hours <= 24:
            return 5.0
        if hours <= 72:
            return 3.0
        if hours <= 168:
            return 1.0
        return 0.0
