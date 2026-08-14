from __future__ import annotations

from revenue_operations.models.types import OperationalMetrics, RevenueOperationsInput


class OperationalMetricsEngine:
    def compute(self, item: RevenueOperationsInput) -> OperationalMetrics:
        opps = item.opportunities
        n = max(1, len(opps))
        qualified = sum(1 for o in opps if o.probability >= 40)
        enriched = sum(1 for o in opps if o.technologies or o.company_size)
        with_dm = sum(1 for o in opps if o.decision_makers)
        replied = sum(1 for o in opps if o.reply_waiting or o.meeting_count or o.won)
        meetings = sum(1 for o in opps if o.meeting_count or o.meeting_today)
        proposals = sum(1 for o in opps if o.proposal_count or o.proposal_pending)
        won = sum(1 for o in opps if o.won)
        revenue = float(item.revenue_closed) + sum(o.pipeline_value for o in opps if o.won)
        avg_deal = revenue / won if won else (sum(o.pipeline_value for o in opps) / n)
        cycle = sum(o.sales_cycle_days or o.days_in_stage for o in opps) / n
        velocity = (sum(o.pipeline_value for o in opps if not o.lost) / max(1.0, cycle)) if cycle else 0.0
        cac = float((item.agency_stats or {}).get("cac") or 2500.0)
        ltv = float((item.agency_stats or {}).get("ltv") or max(avg_deal * 1.4, 20000.0))
        roi = ((ltv - cac) / cac * 100.0) if cac else 0.0
        return OperationalMetrics(
            discovery_rate=100.0,
            qualification_rate=round(qualified / n * 100.0, 2),
            enrichment_rate=round(enriched / n * 100.0, 2),
            decision_maker_success=round(with_dm / n * 100.0, 2),
            reply_rate=round(replied / n * 100.0, 2),
            meeting_rate=round(meetings / n * 100.0, 2),
            proposal_rate=round(proposals / n * 100.0, 2),
            close_rate=round(won / n * 100.0, 2),
            revenue=round(revenue, 2),
            average_deal_size=round(avg_deal, 2),
            sales_cycle_days=round(cycle, 2),
            pipeline_velocity=round(velocity, 2),
            customer_acquisition_cost=round(cac, 2),
            lifetime_value=round(ltv, 2),
            roi=round(roi, 2),
            evidence=[f"n:{len(opps)}", f"won:{won}", f"revenue:{revenue}"],
        )
