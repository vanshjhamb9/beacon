from __future__ import annotations

from revenue_operations.models.types import (
    AgentMessage,
    AgentRole,
    AgentRunResult,
    RevenueOperationsInput,
)


class MultiAgentOrchestrator:
    """Deterministic internal agents exchanging structured outputs only."""

    ROLES = list(AgentRole)

    def run(self, item: RevenueOperationsInput) -> list[AgentRunResult]:
        opps = item.opportunities
        results: list[AgentRunResult] = []
        research = AgentRunResult(
            agent=AgentRole.RESEARCH,
            outputs={"signals_scanned": len(opps), "industries": sorted({o.industry for o in opps if o.industry})[:8]},
            messages=[
                AgentMessage(
                    from_agent=AgentRole.RESEARCH,
                    to_agent=AgentRole.QUALIFICATION,
                    topic="research_complete",
                    payload={"count": len(opps)},
                    evidence=["agent:research"],
                )
            ],
            evidence=["role:research"],
        )
        qualification = AgentRunResult(
            agent=AgentRole.QUALIFICATION,
            outputs={
                "qualified": sum(1 for o in opps if o.probability >= 40),
                "a_plus": sum(1 for o in opps if o.probability >= 75),
            },
            messages=[
                AgentMessage(
                    from_agent=AgentRole.QUALIFICATION,
                    to_agent=AgentRole.ENRICHMENT,
                    topic="qualified_accounts",
                    payload={"qualified": sum(1 for o in opps if o.probability >= 40)},
                    evidence=["agent:qualification"],
                )
            ],
            evidence=["role:qualification"],
        )
        enrichment = AgentRunResult(
            agent=AgentRole.ENRICHMENT,
            outputs={"enriched": sum(1 for o in opps if o.technologies or o.company_size)},
            messages=[
                AgentMessage(
                    from_agent=AgentRole.ENRICHMENT,
                    to_agent=AgentRole.DECISION_MAKER,
                    topic="enrichment_ready",
                    payload={},
                    evidence=["agent:enrichment"],
                )
            ],
            evidence=["role:enrichment"],
        )
        decision_maker = AgentRunResult(
            agent=AgentRole.DECISION_MAKER,
            outputs={"with_dms": sum(1 for o in opps if o.decision_makers)},
            messages=[
                AgentMessage(
                    from_agent=AgentRole.DECISION_MAKER,
                    to_agent=AgentRole.REVENUE,
                    topic="decision_makers_ready",
                    payload={},
                    evidence=["agent:decision_maker"],
                )
            ],
            evidence=["role:decision_maker"],
        )
        revenue = AgentRunResult(
            agent=AgentRole.REVENUE,
            outputs={
                "pipeline": sum(o.pipeline_value for o in opps if not o.lost),
                "expected": sum(o.pipeline_value * o.probability / 100.0 for o in opps if not o.lost),
            },
            messages=[
                AgentMessage(
                    from_agent=AgentRole.REVENUE,
                    to_agent=AgentRole.SALES,
                    topic="pipeline_snapshot",
                    payload={},
                    evidence=["agent:revenue"],
                )
            ],
            evidence=["role:revenue"],
        )
        sales = AgentRunResult(
            agent=AgentRole.SALES,
            outputs={
                "meetings": sum(1 for o in opps if o.meeting_today),
                "proposals": sum(1 for o in opps if o.proposal_pending),
                "negotiations": sum(1 for o in opps if o.negotiation),
            },
            messages=[
                AgentMessage(
                    from_agent=AgentRole.SALES,
                    to_agent=AgentRole.CAMPAIGN,
                    topic="sales_queue",
                    payload={},
                    evidence=["agent:sales"],
                )
            ],
            evidence=["role:sales"],
        )
        campaign = AgentRunResult(
            agent=AgentRole.CAMPAIGN,
            outputs={"campaigns_running": item.campaigns_running},
            messages=[
                AgentMessage(
                    from_agent=AgentRole.CAMPAIGN,
                    to_agent=AgentRole.COMMUNICATION,
                    topic="campaign_status",
                    payload={"running": item.campaigns_running},
                    evidence=["agent:campaign"],
                )
            ],
            evidence=["role:campaign"],
        )
        communication = AgentRunResult(
            agent=AgentRole.COMMUNICATION,
            outputs={"replies_waiting": sum(1 for o in opps if o.reply_waiting)},
            messages=[
                AgentMessage(
                    from_agent=AgentRole.COMMUNICATION,
                    to_agent=AgentRole.FOUNDER,
                    topic="inbox_summary",
                    payload={},
                    evidence=["agent:communication"],
                )
            ],
            evidence=["role:communication"],
        )
        founder = AgentRunResult(
            agent=AgentRole.FOUNDER,
            outputs={
                "mission": "Approve, meet, propose, close",
                "focus_count": sum(
                    1
                    for o in opps
                    if o.meeting_today or o.proposal_pending or o.negotiation or (o.reply_waiting and o.probability >= 70)
                ),
            },
            messages=[],
            evidence=["role:founder", "no_gpt:true"],
        )
        results.extend(
            [research, qualification, enrichment, decision_maker, revenue, sales, campaign, communication, founder]
        )
        return results
