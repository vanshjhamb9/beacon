from __future__ import annotations

from datetime import UTC, datetime

from revenue_operations.models.types import OpportunitySignal, ReplayEvent, RevenueOperationsInput, RevenueReplay


STAGE_ORDER = [
    ("lead_discovered", "Lead discovered"),
    ("research", "Research"),
    ("qualification", "Qualification"),
    ("email", "Email"),
    ("reply", "Reply"),
    ("meeting", "Meeting"),
    ("proposal", "Proposal"),
    ("negotiation", "Negotiation"),
    ("won", "Won"),
    ("lost", "Lost"),
]


class RevenueReplayEngine:
    def build(self, item: RevenueOperationsInput) -> list[RevenueReplay]:
        return [self.replay_opportunity(o, now=item.now) for o in item.opportunities]

    def replay_opportunity(self, opp: OpportunitySignal, *, now: datetime | None = None) -> RevenueReplay:
        ts = now or datetime.now(UTC)
        events: list[ReplayEvent] = [
            ReplayEvent(stage="lead_discovered", title="Lead discovered", detail=opp.company_name, occurred_at=ts, evidence=["stage:discovered"]),
            ReplayEvent(stage="research", title="Research", detail=opp.industry or "Research complete", occurred_at=ts, evidence=["stage:research"]),
            ReplayEvent(
                stage="qualification",
                title="Qualification",
                detail=f"Probability {opp.probability}",
                occurred_at=ts,
                evidence=[f"prob:{opp.probability}"],
            ),
        ]
        if opp.stage or True:
            events.append(ReplayEvent(stage="email", title="Email", detail=opp.campaign_name or "Outreach", occurred_at=ts, evidence=["channel:email"]))
        if opp.reply_waiting or opp.meeting_count or opp.won or opp.lost:
            events.append(ReplayEvent(stage="reply", title="Reply", detail="Inbound engagement", occurred_at=ts, evidence=["channel:reply"]))
        if opp.meeting_today or opp.meeting_count:
            events.append(
                ReplayEvent(
                    stage="meeting",
                    title="Meeting",
                    detail=f"{opp.meeting_count} meeting(s)",
                    occurred_at=ts,
                    evidence=["channel:meeting"],
                )
            )
        if opp.proposal_pending or opp.proposal_count:
            events.append(
                ReplayEvent(
                    stage="proposal",
                    title="Proposal",
                    detail=f"{opp.proposal_count} proposal(s)",
                    occurred_at=ts,
                    evidence=["channel:proposal"],
                )
            )
        if opp.negotiation:
            events.append(ReplayEvent(stage="negotiation", title="Negotiation", detail="Commercial negotiation", occurred_at=ts, evidence=["stage:negotiation"]))
        outcome = None
        if opp.won:
            outcome = "won"
            events.append(ReplayEvent(stage="won", title="Won", detail=opp.why_won or "Closed won", occurred_at=ts, evidence=["outcome:won"]))
        if opp.lost:
            outcome = "lost"
            events.append(ReplayEvent(stage="lost", title="Lost", detail=opp.why_lost or "Closed lost", occurred_at=ts, evidence=["outcome:lost"]))
        return RevenueReplay(
            opportunity_id=opp.opportunity_id,
            company_id=opp.company_id,
            company_name=opp.company_name,
            events=events,
            outcome=outcome,
            evidence=[f"events:{len(events)}", f"company:{opp.company_name}"],
        )
