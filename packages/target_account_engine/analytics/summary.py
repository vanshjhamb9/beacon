from __future__ import annotations

from collections import Counter
from typing import Any

from target_account_engine.models.types import TargetAccountDecision


class TargetAccountAnalytics:
    def summarize(self, decisions: list[TargetAccountDecision]) -> dict[str, Any]:
        if not decisions:
            return {
                "total": 0,
                "tiers": {},
                "industries": {},
                "countries": {},
                "avg_revenue_score": 0.0,
                "hunter_triggered": 0,
                "top_services": {},
                "pipeline_ready": 0,
            }
        tiers = Counter(d.tier.value for d in decisions)
        services = Counter(d.service_match or "unknown" for d in decisions)
        industries = Counter(
            (d.explanations.get("industry") or "unknown") for d in decisions
        )
        return {
            "total": len(decisions),
            "tiers": dict(tiers),
            "industries": dict(industries),
            "countries": {},
            "avg_revenue_score": round(
                sum(d.revenue_opportunity_score for d in decisions) / len(decisions), 2
            ),
            "hunter_triggered": sum(1 for d in decisions if d.hunter_triggered),
            "top_services": dict(services.most_common(10)),
            "pipeline_ready": sum(1 for d in decisions if d.proceed_to_copilot),
            "heat": [
                {
                    "company_id": str(d.company_id),
                    "company_name": d.company_name,
                    "score": d.revenue_opportunity_score,
                    "tier": d.tier.value,
                    "icp": d.matched_icp_key,
                }
                for d in sorted(decisions, key=lambda x: x.revenue_opportunity_score, reverse=True)[:50]
            ],
        }
