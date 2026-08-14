from __future__ import annotations

from production_validation.models.types import OutcomeLearningSnapshot, ProductionValidationInput, RevenueHealthSnapshot


class RevenueMetricsEngine:
    def snapshot(self, item: ProductionValidationInput) -> RevenueHealthSnapshot:
        m = item.revenue_metrics or {}
        funnel = item.funnel or {}
        won = float(m.get("won") or funnel.get("won") or 0)
        lost = float(m.get("lost") or funnel.get("lost") or 0)
        closed = float(m.get("revenue_closed") or m.get("revenue") or 0.0)
        pipeline = float(m.get("pipeline_value") or 0.0)
        replies = int(m.get("replies") or funnel.get("replies") or 0)
        meetings = int(m.get("meetings") or funnel.get("meetings") or 0)
        proposals = int(m.get("proposals") or funnel.get("proposals") or 0)
        campaigns = int(m.get("campaigns") or len(item.campaigns) or 0)
        win_rate = (won / (won + lost) * 100.0) if (won + lost) else float(m.get("win_rate") or 0.0)
        avg_deal = float(m.get("average_deal_size") or (closed / won if won else 0.0))
        cycle = float(m.get("average_sales_cycle_days") or 28.0)
        forecast = float(m.get("forecast") or (pipeline * max(win_rate, 1.0) / 100.0))
        return RevenueHealthSnapshot(
            revenue_today=float(m.get("revenue_today") or 0.0),
            pipeline_value=pipeline,
            qualified_companies=int(m.get("qualified_companies") or 0),
            sales_ready=int(m.get("sales_ready") or 0),
            campaigns=campaigns,
            replies=replies,
            meetings=meetings,
            proposals=proposals,
            revenue_closed=closed,
            win_rate=round(win_rate, 4),
            average_deal_size=round(avg_deal, 4),
            average_sales_cycle_days=round(cycle, 4),
            forecast=round(forecast, 4),
            evidence=[f"pipeline:{pipeline}", f"win_rate:{win_rate}", f"forecast:{forecast}"],
        )


class OutcomeLearningEngine:
    """Compose outcome rates into recommendations — never auto-applies rules."""

    def snapshot(self, item: ProductionValidationInput) -> OutcomeLearningSnapshot:
        rates = item.outcome_rates or {}
        reply = float(rates.get("reply_rate") or item.reply_rate or 0.0)
        meeting = float(rates.get("meeting_rate") or 0.0)
        proposal = float(rates.get("proposal_rate") or 0.0)
        win = float(rates.get("win_rate") or 0.0)
        recs: list[str] = []
        if reply < 0.08:
            recs.append("Improve personalization and pain-first openings (approval required).")
        if meeting < 0.2 and reply >= 0.08:
            recs.append("Strengthen meeting CTA and Calendly placement (approval required).")
        if proposal < 0.3 and meeting >= 0.2:
            recs.append("Ship proposal packs within 24h of meetings (approval required).")
        if win < 0.15 and proposal >= 0.3:
            recs.append("Tighten pricing guidance and objection playbooks (approval required).")
        if not recs:
            recs.append("Maintain current playbooks; continue measuring weekly cohorts.")
        return OutcomeLearningSnapshot(
            reply_rate=reply,
            meeting_rate=meeting,
            proposal_rate=proposal,
            win_rate=win,
            industry_success=dict(rates.get("industry_success") or {}),
            service_success=dict(rates.get("service_success") or {}),
            persona_success=dict(rates.get("persona_success") or {}),
            subject_line_success=dict(rates.get("subject_line_success") or {}),
            cta_success=dict(rates.get("cta_success") or {}),
            recommendations=recs,
            requires_human_approval=True,
            evidence=[f"reply_rate:{reply}", f"meeting_rate:{meeting}", f"win_rate:{win}"],
        )
