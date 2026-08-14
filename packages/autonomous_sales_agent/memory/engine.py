from __future__ import annotations

from autonomous_sales_agent.models.types import AutonomousSalesAgentInput, SalesMemoryInsight


class SalesMemoryEngine:
    """Observe conversion patterns without modifying existing engines."""

    def insights(self, item: AutonomousSalesAgentInput) -> SalesMemoryInsight:
        mem = item.memory_signals or {}
        return SalesMemoryInsight(
            best_email_pattern=str(mem.get("best_email_pattern") or "pain-first + single CTA"),
            best_cta=str(mem.get("best_cta") or "Book a 20-min discovery"),
            best_follow_up_interval_days=int(mem.get("best_follow_up_interval_days") or item.follow_up_config.follow_up_days),
            best_industries=list(mem.get("best_industries") or ([item.industry] if item.industry else ["SaaS", "Healthcare"])),
            best_company_sizes=list(mem.get("best_company_sizes") or ([item.company_size] if item.company_size else ["51-200"])),
            best_founders=list(mem.get("best_founders") or [dm.get("name") for dm in item.decision_makers if dm.get("name")][:3]),
            best_service=str(mem.get("best_service") or item.recommended_service or "AI Automation"),
            best_conversion_source=str(mem.get("best_conversion_source") or "Revenue Hunter A+"),
            evidence=[
                "mode:observe_only",
                "no_engine_mutation:true",
                f"service:{item.recommended_service or 'n/a'}",
            ],
        )
