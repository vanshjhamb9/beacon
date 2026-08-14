from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sales_readiness.models.types import (
    BuyingIntent,
    ContactCompleteness,
    IdentityCompleteness,
    TechnologyReadiness,
    TrustBreakdown,
    WebsiteIntelligence,
)


class SalesTrustEngine:
    """Composite trust 0–100 from observed identity/tech/intent/contacts/website/source/verification/freshness."""

    WEIGHTS = {
        "identity": 15.0,
        "technology": 10.0,
        "intent": 15.0,
        "contacts": 20.0,
        "website": 10.0,
        "source": 10.0,
        "verification": 10.0,
        "freshness": 10.0,
    }

    def score(
        self,
        *,
        identity: IdentityCompleteness,
        technology: TechnologyReadiness,
        intent: BuyingIntent,
        contacts: ContactCompleteness,
        website: WebsiteIntelligence,
        payload: dict[str, Any],
    ) -> TrustBreakdown:
        identity_s = 15.0 if identity.identity_complete else max(0.0, 15.0 - 3.0 * len(identity.missing_fields))
        tech_s = min(10.0, technology.maturity_score / 10.0)
        intent_s = min(15.0, intent.score / 100.0 * 15.0)
        contact_s = min(20.0, contacts.coverage_percent / 100.0 * 12.0 + contacts.verified_email_count * 4.0)
        website_s = min(10.0, website.score / 10.0)
        source_s = 10.0 if payload.get("source") else 0.0
        verification_s = min(10.0, float(payload.get("verification_score") or 0.0) / 10.0)
        freshness_s = self._freshness(payload.get("last_seen_at") or payload.get("collected_at"))

        overall = round(
            identity_s + tech_s + intent_s + contact_s + website_s + source_s + verification_s + freshness_s,
            2,
        )
        return TrustBreakdown(
            identity=round(identity_s, 2),
            technology=round(tech_s, 2),
            intent=round(intent_s, 2),
            contacts=round(min(20.0, contact_s), 2),
            website=round(website_s, 2),
            source=source_s,
            verification=round(verification_s, 2),
            freshness=freshness_s,
            overall=min(100.0, overall),
            evidence=[
                f"identity:{identity_s}",
                f"technology:{tech_s}",
                f"intent:{intent_s}",
                f"contacts:{contact_s}",
                f"website:{website_s}",
                f"source:{source_s}",
                f"verification:{verification_s}",
                f"freshness:{freshness_s}",
                f"overall:{overall}",
            ],
        )

    def _freshness(self, value: Any) -> float:
        if value is None:
            return 0.0
        try:
            dt = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            hours = (datetime.now(UTC) - dt.astimezone(UTC)).total_seconds() / 3600.0
        except Exception:  # noqa: BLE001
            return 0.0
        if hours <= 24:
            return 10.0
        if hours <= 72:
            return 7.0
        if hours <= 168:
            return 4.0
        return 1.0
