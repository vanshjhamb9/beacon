from __future__ import annotations

from uuid import uuid4

from founder_os.models.types import FounderOsInput, FounderRecommendation, SalesKPISnapshot


class FounderRecommendationEngine:
    """Morning recommendations from deterministic evidence only — no hallucinations."""

    def generate(self, data: FounderOsInput, kpis: SalesKPISnapshot) -> list[FounderRecommendation]:
        recs: list[FounderRecommendation] = []

        if data.industry_wins:
            top_ind, top_n = max(data.industry_wins.items(), key=lambda kv: (kv[1], kv[0]))
            total = sum(data.industry_wins.values()) or 1
            share = round((top_n / total) * 100.0, 2)
            if top_n >= 2 and share >= 30.0:
                recs.append(
                    FounderRecommendation(
                        recommendation_id=str(uuid4()),
                        title=f"{top_ind} companies are converting better",
                        action=f"Increase {top_ind} priority in ICP filters",
                        reason=f"{top_ind} accounts for {share}% of wins ({top_n}/{total}).",
                        evidence=[f"industry_wins:{top_ind}:{top_n}", f"share_pct:{share}"],
                        impact_metric="Qualified Opportunities",
                        confidence=min(95.0, 50.0 + top_n * 8.0),
                    )
                )

        funding_signals = data.new_buying_signals  # proxy; evidence from style wins if present
        hiring_proxy = data.outreach_style_wins.get("hiring", 0)
        funding_proxy = data.outreach_style_wins.get("funding", 0) or data.subject_line_wins.get("funding", 0)
        if funding_proxy > hiring_proxy and funding_proxy >= 2:
            recs.append(
                FounderRecommendation(
                    recommendation_id=str(uuid4()),
                    title="Funding signals outperform hiring",
                    action="Increase funding weight in urgency / why-now scoring",
                    reason=f"Funding-tagged wins={funding_proxy} vs hiring-tagged={hiring_proxy}.",
                    evidence=[f"funding_wins:{funding_proxy}", f"hiring_wins:{hiring_proxy}"],
                    impact_metric="Reply Rate",
                    confidence=min(92.0, 55.0 + funding_proxy * 6.0),
                )
            )

        website_tasks = len(data.website_audit_needed)
        if website_tasks >= 1 and kpis.reply_rate >= 20.0:
            recs.append(
                FounderRecommendation(
                    recommendation_id=str(uuid4()),
                    title="Website audits correlate with reply opportunity",
                    action="Increase website intelligence coverage on A+/A accounts",
                    reason=(
                        f"{website_tasks} accounts need audits while reply rate is {kpis.reply_rate:.1f}%."
                    ),
                    evidence=[f"website_audit_needed:{website_tasks}", f"reply_rate:{kpis.reply_rate}"],
                    impact_metric="Reply Rate",
                    confidence=min(88.0, 45.0 + website_tasks * 5.0 + kpis.reply_rate * 0.2),
                )
            )

        if data.service_wins:
            top_svc, svc_n = max(data.service_wins.items(), key=lambda kv: (kv[1], kv[0]))
            recs.append(
                FounderRecommendation(
                    recommendation_id=str(uuid4()),
                    title=f"{top_svc} is the top converting service",
                    action=f"Lead morning pitches with {top_svc} where evidence matches",
                    reason=f"{top_svc} leads service wins with {svc_n} conversions.",
                    evidence=[f"service_wins:{top_svc}:{svc_n}"],
                    impact_metric="Proposal Conversion",
                    confidence=min(90.0, 48.0 + svc_n * 7.0),
                )
            )

        if kpis.pipeline_health < 45.0:
            recs.append(
                FounderRecommendation(
                    recommendation_id=str(uuid4()),
                    title="Pipeline health is weak",
                    action="Clear campaign approvals and reply queue before net-new outreach",
                    reason=f"Pipeline health score is {kpis.pipeline_health:.1f}/100.",
                    evidence=[f"pipeline_health:{kpis.pipeline_health}", f"campaigns_waiting:{data.campaigns_waiting_approval}"],
                    impact_metric="Meetings Booked",
                    confidence=80.0,
                )
            )

        if data.campaigns_waiting_approval >= 3:
            recs.append(
                FounderRecommendation(
                    recommendation_id=str(uuid4()),
                    title="Campaign approval backlog",
                    action="Approve or reject waiting campaigns in the next 4 hours",
                    reason=f"{data.campaigns_waiting_approval} campaigns blocked on founder approval.",
                    evidence=[f"campaigns_waiting:{data.campaigns_waiting_approval}"],
                    impact_metric="Meetings Booked",
                    confidence=85.0,
                )
            )

        # Drop any recommendation lacking evidence (hard rule)
        return [r for r in recs if r.evidence]
