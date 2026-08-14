from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign
from app.models.decision import DecisionMaker
from app.models.intelligence import Company
from app.models.opportunity import Opportunity
from app.models.outcomes import Deal, Meeting, Proposal
from app.models.revenue_hunter import RevenueHunterDossier
from app.models.revenue_operations import (
    AgencyStatisticRow,
    LearningRecommendationRow,
    RevenueAlertRow,
    RevenueForecastRow,
    RevenueMemoryRow,
    RevenueMetricRow,
    RevenueOperationSnapshot,
    RevenueReplayRow,
)
from app.models.sales_intelligence import SalesIntelligenceSnapshot
from revenue_operations.models.types import (
    OpportunitySignal,
    RevenueOperationsDecision,
    RevenueOperationsInput,
)


class RevenueOperationsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def build_input(self) -> RevenueOperationsInput:
        opportunities = list(
            (await self.session.execute(select(Opportunity).order_by(Opportunity.updated_at.desc()).limit(200)))
            .scalars()
            .all()
        )
        campaigns = list(
            (await self.session.execute(select(Campaign).order_by(Campaign.created_at.desc()).limit(100))).scalars().all()
        )
        running = sum(1 for c in campaigns if c.status in {"approved", "scheduled", "running", "completed"})
        existing_keys = list(
            (
                await self.session.execute(
                    select(RevenueAlertRow.dedupe_key).where(RevenueAlertRow.lifecycle.in_(["new", "viewed"]))
                )
            )
            .scalars()
            .all()
        )

        signals: list[OpportunitySignal] = []
        for opp in opportunities:
            company = await self.session.get(Company, opp.company_id) if opp.company_id else None
            dossier = await self.session.scalar(
                select(RevenueHunterDossier)
                .where(RevenueHunterDossier.company_id == opp.company_id)
                .order_by(RevenueHunterDossier.created_at.desc())
                .limit(1)
            )
            si = await self.session.scalar(
                select(SalesIntelligenceSnapshot)
                .where(SalesIntelligenceSnapshot.company_id == opp.company_id)
                .order_by(SalesIntelligenceSnapshot.created_at.desc())
                .limit(1)
            )
            dms = list(
                (
                    await self.session.execute(
                        select(DecisionMaker).where(DecisionMaker.company_id == opp.company_id).limit(5)
                    )
                )
                .scalars()
                .all()
            )
            meetings = await self.session.scalar(
                select(func.count()).select_from(Meeting).where(Meeting.company_id == opp.company_id)
            ) or 0
            proposals = await self.session.scalar(
                select(func.count()).select_from(Proposal).where(Proposal.company_id == opp.company_id)
            ) or 0
            campaign = next((c for c in campaigns if c.company_id == opp.company_id), None)
            attrs = (company.attributes if company else {}) or {}
            si_payload = (si.payload if si else {}) or {}
            intent = float(
                (si_payload.get("buying_intent") or {}).get("buying_intent_score")
                or (si.buying_intent_score if si else 0)
                or getattr(opp, "opportunity_score", 0)
                or 0
            )
            radar_hints = list(attrs.get("radar_hints") or [])
            if dossier and dossier.pain_points:
                radar_hints.extend(str(p.get("pain") if isinstance(p, dict) else p) for p in dossier.pain_points[:4])
            signals.append(
                OpportunitySignal(
                    opportunity_id=opp.id,
                    company_id=opp.company_id,
                    company_name=(company.name if company else None) or getattr(opp, "company_name", None) or "Unknown",
                    industry=(company.industry if company else None) or (dossier.industry if dossier else None),
                    service=(dossier.recommended_service if dossier else None),
                    stage=str(getattr(opp, "status", None) or attrs.get("stage") or "open"),
                    probability=float(dossier.probability if dossier else intent or getattr(opp, "opportunity_score", 0) or 0),
                    pipeline_value=float(attrs.get("pipeline_value") or (intent * 500.0) or 15000.0),
                    days_in_stage=int(attrs.get("days_in_stage") or 1),
                    reply_waiting=bool(attrs.get("reply_waiting")),
                    meeting_today=bool(attrs.get("meeting_today")),
                    proposal_pending=bool(attrs.get("proposal_pending")),
                    negotiation=bool(attrs.get("negotiation")),
                    at_risk=bool(attrs.get("at_risk")) or (int(attrs.get("days_in_stage") or 0) >= 10 and intent < 40),
                    won=bool(attrs.get("won")) or str(getattr(opp, "status", "")).lower() == "won",
                    lost=bool(attrs.get("lost")) or str(getattr(opp, "status", "")).lower() == "lost",
                    radar_hints=[h for h in radar_hints if h][:12],
                    objections=list(attrs.get("objections") or [])[:8],
                    decision_makers=[dm.name for dm in dms if dm.name],
                    lead_source=str(attrs.get("lead_source") or "Revenue Hunter"),
                    campaign_name=campaign.company_name if campaign else None,
                    country=str(attrs.get("country") or "") or None,
                    company_size=str(attrs.get("company_size") or "") or None,
                    technologies=list(attrs.get("technologies") or [])[:10],
                    meeting_count=int(meetings),
                    proposal_count=int(proposals),
                    reply_speed_hours=float(attrs.get("reply_speed_hours") or 0),
                    sales_cycle_days=int(attrs.get("sales_cycle_days") or 0),
                    why_won=str(attrs.get("why_won") or "") or None,
                    why_lost=str(attrs.get("why_lost") or "") or None,
                    competitor=str(attrs.get("competitor") or "") or None,
                    budget=(dossier.expected_budget if dossier else None) or str(attrs.get("budget") or "") or None,
                    timeline=str(attrs.get("timeline") or "") or None,
                    founder_notes=list(attrs.get("founder_notes") or []),
                )
            )

        closed = await self.session.scalar(select(func.coalesce(func.sum(Deal.value), 0))) or 0
        industries = {}
        services = {}
        for s in signals:
            if s.industry:
                industries[s.industry] = industries.get(s.industry, 0) + 1
            if s.service:
                services[s.service] = services.get(s.service, 0) + 1

        return RevenueOperationsInput(
            opportunities=signals,
            campaigns_running=running,
            revenue_today=float(sum(s.pipeline_value * s.probability / 100.0 for s in signals if s.meeting_today) * 0.2),
            revenue_closed=float(closed),
            top_industries=[k for k, _ in sorted(industries.items(), key=lambda x: -x[1])][:8],
            top_services=[k for k, _ in sorted(services.items(), key=lambda x: -x[1])][:8],
            top_campaign=campaigns[0].company_name if campaigns else None,
            top_lead_source="Revenue Hunter",
            funnel_counts={
                "discovered": float(len(signals)),
                "qualified": float(sum(1 for s in signals if s.probability >= 40)),
                "replied": float(sum(1 for s in signals if s.reply_waiting or s.won)),
                "meeting": float(sum(1 for s in signals if s.meeting_count or s.meeting_today)),
                "proposal": float(sum(1 for s in signals if s.proposal_count or s.proposal_pending)),
                "won": float(sum(1 for s in signals if s.won)),
            },
            weekly_trend=[{"week": i, "revenue": float(closed) * (0.1 + i * 0.02)} for i in range(1, 9)],
            monthly_trend=[{"month": i, "revenue": float(closed) * (0.2 + i * 0.05)} for i in range(1, 7)],
            existing_alert_keys=[str(k) for k in existing_keys],
            agency_stats={"cac": 2500.0, "ltv": 42000.0},
            now=datetime.now(UTC),
        )

    async def store_decision(self, decision: RevenueOperationsDecision) -> RevenueOperationSnapshot:
        snap = RevenueOperationSnapshot(
            revenue_score=float(decision.command_center.revenue_score),
            pipeline_value=float(decision.control_tower.pipeline_value),
            expected_revenue=float(decision.control_tower.expected_revenue),
            payload=decision.model_dump(mode="json"),
            evidence_chain=list(decision.evidence_chain),
            scoring_version=decision.scoring_version,
            metadata_json={},
        )
        self.session.add(snap)
        await self.session.flush()

        self.session.add(
            RevenueForecastRow(
                this_week=decision.forecast.this_week.amount,
                this_month=decision.forecast.this_month.amount,
                quarter=decision.forecast.quarter.amount,
                annual=decision.forecast.annual.amount,
                confidence_score=decision.forecast.confidence_score,
                pipeline_health=decision.forecast.pipeline_health,
                payload=decision.forecast.model_dump(mode="json"),
                evidence_chain=list(decision.forecast.evidence),
                scoring_version=decision.scoring_version,
            )
        )
        self.session.add(
            RevenueMetricRow(
                payload=decision.operational_metrics.model_dump(mode="json"),
                close_rate=decision.operational_metrics.close_rate,
                reply_rate=decision.operational_metrics.reply_rate,
                meeting_rate=decision.operational_metrics.meeting_rate,
                revenue=decision.operational_metrics.revenue,
                evidence_chain=list(decision.operational_metrics.evidence),
                scoring_version=decision.scoring_version,
            )
        )
        self.session.add(
            AgencyStatisticRow(
                kind="daily",
                payload={
                    "control_tower": decision.control_tower.model_dump(mode="json"),
                    "command_center": decision.command_center.model_dump(mode="json"),
                },
                item_count=len(decision.control_tower.conversion_funnel),
                evidence_chain=list(decision.evidence_chain),
                scoring_version=decision.scoring_version,
            )
        )

        for alert in decision.alerts:
            self.session.add(
                RevenueAlertRow(
                    alert_id=alert.alert_id,
                    kind=alert.kind.value,
                    title=alert.title,
                    severity=alert.severity,
                    company_id=alert.company_id,
                    company_name=alert.company_name,
                    recommendation=alert.recommendation,
                    lifecycle=alert.lifecycle.value,
                    dedupe_key=alert.dedupe_key,
                    evidence=list(alert.evidence),
                    snapshot_id=snap.id,
                )
            )
        for mem in decision.memory_records[:200]:
            self.session.add(
                RevenueMemoryRow(
                    record_type=mem.record_type,
                    company_id=mem.company_id,
                    company_name=mem.company_name,
                    title=mem.title,
                    body=mem.body,
                    tags=list(mem.tags),
                    searchable_text=mem.searchable_text,
                    evidence=list(mem.evidence),
                    immutable=True,
                )
            )
        for replay in decision.replays[:100]:
            self.session.add(
                RevenueReplayRow(
                    opportunity_id=replay.opportunity_id,
                    company_id=replay.company_id,
                    company_name=replay.company_name,
                    outcome=replay.outcome,
                    events=[e.model_dump(mode="json") for e in replay.events],
                    evidence=list(replay.evidence),
                    scoring_version=decision.scoring_version,
                )
            )
        for rec in decision.learning.recommendations:
            existing = await self.session.scalar(
                select(LearningRecommendationRow).where(LearningRecommendationRow.recommendation_id == rec.recommendation_id)
            )
            if existing:
                continue
            self.session.add(
                LearningRecommendationRow(
                    recommendation_id=rec.recommendation_id,
                    category=rec.category,
                    title=rec.title,
                    detail=rec.detail,
                    status=rec.status.value,
                    modifies_production=False,
                    evidence=list(rec.evidence),
                )
            )
        await self.session.flush()
        return snap

    async def latest_snapshot(self) -> RevenueOperationSnapshot | None:
        return await self.session.scalar(
            select(RevenueOperationSnapshot).order_by(RevenueOperationSnapshot.created_at.desc()).limit(1)
        )

    async def latest_forecast(self) -> RevenueForecastRow | None:
        return await self.session.scalar(select(RevenueForecastRow).order_by(RevenueForecastRow.created_at.desc()).limit(1))

    async def latest_metrics(self) -> RevenueMetricRow | None:
        return await self.session.scalar(select(RevenueMetricRow).order_by(RevenueMetricRow.created_at.desc()).limit(1))

    async def list_alerts(self, *, lifecycle: str | None = None, limit: int = 50) -> list[RevenueAlertRow]:
        stmt = select(RevenueAlertRow).order_by(RevenueAlertRow.created_at.desc()).limit(limit)
        if lifecycle:
            stmt = stmt.where(RevenueAlertRow.lifecycle == lifecycle)
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_alert(self, alert_row_id: UUID) -> RevenueAlertRow | None:
        return await self.session.get(RevenueAlertRow, alert_row_id)

    async def search_memory(self, query: str = "", *, limit: int = 50) -> list[RevenueMemoryRow]:
        stmt = select(RevenueMemoryRow).order_by(RevenueMemoryRow.created_at.desc()).limit(limit)
        if query.strip():
            q = f"%{query.strip().lower()}%"
            stmt = stmt.where(or_(func.lower(RevenueMemoryRow.searchable_text).like(q), func.lower(RevenueMemoryRow.title).like(q)))
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_replay(self, replay_id: UUID) -> RevenueReplayRow | None:
        return await self.session.get(RevenueReplayRow, replay_id)

    async def list_learning(self, *, status: str | None = None, limit: int = 50) -> list[LearningRecommendationRow]:
        stmt = select(LearningRecommendationRow).order_by(LearningRecommendationRow.created_at.desc()).limit(limit)
        if status:
            stmt = stmt.where(LearningRecommendationRow.status == status)
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_learning(self, recommendation_id: str) -> LearningRecommendationRow | None:
        return await self.session.scalar(
            select(LearningRecommendationRow)
            .where(LearningRecommendationRow.recommendation_id == recommendation_id)
            .order_by(LearningRecommendationRow.created_at.desc())
            .limit(1)
        )
