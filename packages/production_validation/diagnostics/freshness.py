from __future__ import annotations

from production_validation.models.types import FreshnessReport, FreshnessSignal, ProductionValidationInput


STALE_RULES = (
    "website_changed",
    "leadership_changed",
    "funding_updated",
    "hiring_updated",
    "technology_changed",
    "decision_maker_changed",
    "email_bounced",
    "linkedin_changed",
)


class FreshnessEngine:
    def evaluate(self, item: ProductionValidationInput) -> FreshnessReport | None:
        if item.company_id is None:
            return None
        detected = set(item.stale_signals or [])
        if item.freshness_days > 45:
            detected.add("leadership_changed")
        signals = [
            FreshnessSignal(
                signal=rule,
                detected=rule in detected,
                detail=f"signal:{rule}",
                reenrich_queued=rule in detected,
            )
            for rule in STALE_RULES
        ]
        stale = any(s.detected for s in signals) or item.freshness_days > 30
        return FreshnessReport(
            company_id=item.company_id,
            company_name=item.company_name,
            stale=stale,
            signals=signals,
            evidence=[f"freshness_days:{item.freshness_days}", f"stale:{stale}", f"queued:{sum(1 for s in signals if s.reenrich_queued)}"],
        )
