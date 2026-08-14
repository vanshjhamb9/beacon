from __future__ import annotations

from revenue_operations.models.types import ControlTowerMetrics, RevenueOperationsInput


class RevenueControlTowerEngine:
    """Compose-only control tower — no duplicate business logic."""

    def build(self, item: RevenueOperationsInput) -> ControlTowerMetrics:
        opps = item.opportunities
        pipeline = sum(o.pipeline_value for o in opps if not o.won and not o.lost)
        meetings = sum(1 for o in opps if o.meeting_today)
        replies = sum(1 for o in opps if o.reply_waiting)
        at_risk = sum(1 for o in opps if o.at_risk)
        proposals = sum(1 for o in opps if o.proposal_pending)
        negotiations = sum(1 for o in opps if o.negotiation)
        expected = sum(o.pipeline_value * (o.probability / 100.0) for o in opps if not o.lost)
        forecast = expected * 1.05
        funnel = dict(item.funnel_counts) or {
            "discovered": float(len(opps)),
            "qualified": float(sum(1 for o in opps if (o.probability or 0) >= 40)),
            "replied": float(sum(1 for o in opps if o.reply_waiting or o.meeting_today or o.won)),
            "meeting": float(sum(1 for o in opps if o.meeting_today or o.meeting_count > 0)),
            "proposal": float(sum(1 for o in opps if o.proposal_pending or o.proposal_count > 0)),
            "won": float(sum(1 for o in opps if o.won)),
        }
        industries = item.top_industries or self._top([o.industry for o in opps if o.industry])
        services = item.top_services or self._top([o.service for o in opps if o.service])
        campaign_names = self._top([o.campaign_name for o in opps if o.campaign_name])
        lead_sources = self._top([o.lead_source for o in opps if o.lead_source])
        return ControlTowerMetrics(
            revenue_today=float(item.revenue_today),
            pipeline_value=round(pipeline, 2),
            meetings_today=meetings,
            replies_waiting=replies,
            campaigns_running=int(item.campaigns_running),
            deals_at_risk=at_risk,
            proposals_pending=proposals,
            negotiations=negotiations,
            expected_revenue=round(expected, 2),
            revenue_forecast=round(forecast, 2),
            conversion_funnel=funnel,
            top_industries=industries[:8],
            top_services=services[:8],
            top_campaign=item.top_campaign or (campaign_names[0] if campaign_names else None),
            top_lead_source=item.top_lead_source or (lead_sources[0] if lead_sources else None),
            weekly_trend=list(item.weekly_trend)[:12],
            monthly_trend=list(item.monthly_trend)[:12],
            evidence=[
                f"opps:{len(opps)}",
                f"pipeline:{pipeline}",
                f"campaigns:{item.campaigns_running}",
                "compose:existing_engines",
            ],
        )

    def _top(self, values: list[str | None]) -> list[str]:
        counts: dict[str, int] = {}
        for v in values:
            if not v:
                continue
            counts[v] = counts.get(v, 0) + 1
        return [k for k, _ in sorted(counts.items(), key=lambda x: (-x[1], x[0]))]
