from __future__ import annotations

from datetime import UTC, datetime

from founder_os.models.types import DailyBriefSnapshot, FounderOsInput


def _top_key(counts: dict[str, int]) -> str | None:
    if not counts:
        return None
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]


class DailyBriefEngine:
    """Morning executive brief — deterministic counts + evidence-backed NL summary."""

    def generate(self, data: FounderOsInput) -> DailyBriefSnapshot:
        now = data.now or datetime.now(UTC)
        top_industry = _top_key(data.industry_wins)
        top_service = _top_key(data.service_wins)
        top_style = _top_key(data.outreach_style_wins)
        top_subject = _top_key(data.subject_line_wins)
        top_cta = _top_key(data.cta_wins)

        evidence = [
            f"new_companies:{data.new_companies_found}",
            f"buying_signals:{data.new_buying_signals}",
            f"qualified:{data.qualified_companies}",
            f"sales_ready:{data.sales_ready_accounts}",
            f"a_plus:{data.a_plus_opportunities}",
            f"campaigns_waiting:{data.campaigns_waiting_approval}",
            f"replies_waiting:{data.replies_waiting}",
            f"meetings_today:{data.meetings_today}",
            f"proposals_pending:{data.proposals_pending}",
            f"pipeline:{data.estimated_pipeline:.0f}",
            f"expected_revenue:{data.expected_revenue:.0f}",
            f"won:{data.won_opportunities}",
            f"lost:{data.lost_opportunities}",
        ]
        if top_industry:
            evidence.append(f"top_industry:{top_industry}:{data.industry_wins[top_industry]}")
        if top_service:
            evidence.append(f"top_service:{top_service}:{data.service_wins[top_service]}")

        summary = self._summary(
            data,
            top_industry=top_industry,
            top_service=top_service,
            top_style=top_style,
        )

        return DailyBriefSnapshot(
            new_companies_found=data.new_companies_found,
            new_buying_signals=data.new_buying_signals,
            qualified_companies=data.qualified_companies,
            sales_ready_accounts=data.sales_ready_accounts,
            a_plus_opportunities=data.a_plus_opportunities,
            campaigns_waiting_approval=data.campaigns_waiting_approval,
            replies_waiting=data.replies_waiting,
            meetings_today=data.meetings_today,
            proposals_pending=data.proposals_pending,
            estimated_pipeline=round(data.estimated_pipeline, 2),
            expected_revenue=round(data.expected_revenue, 2),
            lost_opportunities=data.lost_opportunities,
            won_opportunities=data.won_opportunities,
            top_performing_industry=top_industry,
            top_performing_service=top_service,
            top_performing_outreach_style=top_style,
            top_performing_subject_line=top_subject,
            top_performing_cta=top_cta,
            executive_summary=summary,
            evidence=evidence,
            generated_at=now,
        )

    def _summary(
        self,
        data: FounderOsInput,
        *,
        top_industry: str | None,
        top_service: str | None,
        top_style: str | None,
    ) -> str:
        parts = [
            f"Yesterday closed {data.won_opportunities} won and {data.lost_opportunities} lost.",
            f"Today: {data.a_plus_opportunities} A+ opportunities, "
            f"{data.campaigns_waiting_approval} campaigns awaiting approval, "
            f"{data.replies_waiting} replies waiting, {data.meetings_today} meetings.",
            f"Pipeline ${data.estimated_pipeline:,.0f}; expected revenue ${data.expected_revenue:,.0f}.",
        ]
        if top_industry:
            parts.append(f"{top_industry} is the top converting industry.")
        if top_service:
            parts.append(f"{top_service} is the top converting service.")
        if top_style:
            parts.append(f"Best outreach style: {top_style}.")
        parts.append(
            f"Mission: clear {data.campaigns_waiting_approval + data.replies_waiting} "
            f"approval/reply actions and book follow-through on {data.meetings_today} meetings."
        )
        return " ".join(parts)
