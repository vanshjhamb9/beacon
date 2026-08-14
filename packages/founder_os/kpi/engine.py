from __future__ import annotations

from founder_os.models.types import FounderOsInput, SalesKPISnapshot


class SalesKPIEngine:
    """Deterministic sales KPIs from outcome/campaign counters (no GPT)."""

    def calculate(self, data: FounderOsInput) -> SalesKPISnapshot:
        contacted = max(0, data.contacted_count)
        replied = max(0, data.replied_count)
        meetings = max(0, data.meeting_count)
        proposals = max(0, data.proposal_count)
        won = max(0, data.won_opportunities)
        lost = max(0, data.lost_opportunities)
        closed = won + lost

        reply_rate = self._rate(replied, contacted)
        meeting_rate = self._rate(meetings, max(contacted, replied))
        proposal_rate = self._rate(proposals, max(meetings, 1) if meetings else contacted)
        close_rate = self._rate(won, closed if closed else contacted)

        avg_deal = float(data.average_deal_size or 0.0)
        velocity = float(data.average_sales_cycle_days or 0.0)
        forecast = round(data.expected_revenue or (data.estimated_pipeline * close_rate / 100.0), 2)

        # Pipeline health: blend coverage, conversion, and activity
        coverage = min(100.0, (data.estimated_pipeline / max(avg_deal, 1.0)) * 10.0) if avg_deal else 50.0
        health = round(
            min(
                100.0,
                coverage * 0.35 + reply_rate * 0.2 + meeting_rate * 0.2 + close_rate * 0.15 + min(10.0, data.meetings_today) * 1.0,
            ),
            4,
        )

        campaign_perf = {
            "send_to_reply": self._rate(data.campaign_replies, data.campaign_sends),
            "sends": float(data.campaign_sends),
            "replies": float(data.campaign_replies),
        }
        service_perf = {k: float(v) for k, v in sorted(data.service_wins.items(), key=lambda kv: -kv[1])}
        country_perf = {k: float(v) for k, v in sorted(data.country_wins.items(), key=lambda kv: -kv[1])}
        industry_perf = {k: float(v) for k, v in sorted(data.industry_wins.items(), key=lambda kv: -kv[1])}

        evidence = [
            f"reply_rate:{reply_rate}",
            f"meeting_rate:{meeting_rate}",
            f"proposal_rate:{proposal_rate}",
            f"close_rate:{close_rate}",
            f"avg_deal:{avg_deal}",
            f"velocity_days:{velocity}",
            f"forecast:{forecast}",
            f"pipeline_health:{health}",
        ]
        return SalesKPISnapshot(
            reply_rate=reply_rate,
            meeting_rate=meeting_rate,
            proposal_rate=proposal_rate,
            close_rate=close_rate,
            average_deal_size=round(avg_deal, 2),
            sales_velocity_days=round(velocity, 2),
            revenue_forecast=forecast,
            pipeline_health=health,
            campaign_performance=campaign_perf,
            service_performance=service_perf,
            country_performance=country_perf,
            industry_performance=industry_perf,
            evidence=evidence,
        )

    def _rate(self, num: int, den: int) -> float:
        if den <= 0:
            return 0.0
        return round(min(100.0, (num / den) * 100.0), 4)
