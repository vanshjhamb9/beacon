from __future__ import annotations

from global_opportunity_acquisition.models.types import CompanyObservation, FreshnessScore


class FreshnessEngine:
    def score(self, company: CompanyObservation, *, source_count: int = 1) -> FreshnessScore:
        hours = max(0.0, float(company.last_seen_hours))
        time_factor = max(0.0, 100.0 - hours * 2.0)
        source_factor = min(100.0, 40.0 + source_count * 12.0)
        verification = 90.0 if company.verified else 55.0
        activity = max(0.0, min(100.0, float(company.activity_score)))
        last_seen = time_factor
        engagement = max(0.0, min(100.0, float(company.engagement_score)))
        score = (
            time_factor * 0.25
            + source_factor * 0.15
            + verification * 0.15
            + activity * 0.15
            + last_seen * 0.15
            + engagement * 0.15
        )
        factors = {
            "time": round(time_factor, 2),
            "source": round(source_factor, 2),
            "verification": round(verification, 2),
            "activity": round(activity, 2),
            "last_seen": round(last_seen, 2),
            "engagement": round(engagement, 2),
        }
        return FreshnessScore(
            score=round(max(0.0, min(100.0, score)), 2),
            factors=factors,
            evidence=[f"hours:{hours}", f"sources:{source_count}"],
        )
