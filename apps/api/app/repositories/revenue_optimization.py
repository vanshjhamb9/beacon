from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.intelligence import Company
from app.models.revenue_optimization import (
    ROIPCTAPerformanceRow,
    ROIPCaseStudyMetricsRow,
    ROIPEmailMetricsRow,
    ROIPFollowupPatternRow,
    ROIPFounderMetricsRow,
    ROIPIndustryMetricsRow,
    ROIPLearningEventRow,
    ROIPOfferMetricsRow,
    ROIPRecommendationRow,
    ROIPReplyAnalysisRow,
    ROIPRevenueBenchmarkRow,
    ROIPSubjectPerformanceRow,
)
from revenue_optimization import RevenueOptimizationService
from revenue_optimization.models.types import OutreachEvent, ROIPDecision, ROIPInput


class RevenueOptimizationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def build_input(self, *, limit: int = 100) -> ROIPInput:
        companies = list(
            (await self.session.execute(select(Company).order_by(Company.updated_at.desc()).limit(limit))).scalars().all()
        )
        events: list[OutreachEvent] = []
        for i, company in enumerate(companies):
            attrs = company.attributes or {}
            events.append(
                OutreachEvent(
                    event_id=f"{company.id}-email",
                    company_id=company.id,
                    company_name=company.name,
                    campaign_id=str(attrs.get("campaign_id") or "default"),
                    industry=company.industry,
                    company_size_band=str(attrs.get("company_size_band") or "") or None,
                    channel=str(attrs.get("channel") or "email"),
                    subject=str(attrs.get("subject") or f"Quick idea for {company.name}"),
                    cta=str(attrs.get("cta") or "book_meeting"),
                    offer=str(attrs.get("offer") or "AI Automation"),
                    delivered=bool(attrs.get("delivered", True)),
                    opened=bool(attrs.get("opened", i % 2 == 0)),
                    open_count=int(attrs.get("open_count") or (2 if i % 5 == 0 else (1 if i % 2 == 0 else 0))),
                    open_hour=int(attrs["open_hour"]) if attrs.get("open_hour") is not None else (9 if i % 2 == 0 else None),
                    open_weekday=int(attrs["open_weekday"]) if attrs.get("open_weekday") is not None else (1 if i % 3 == 0 else 2),
                    open_device=str(attrs.get("open_device") or "") or None,
                    open_country=str(attrs.get("open_country") or "") or None,
                    calendly_clicks=int(attrs.get("calendly_clicks") or 0),
                    website_visits=int(attrs.get("website_visits") or 0),
                    replied=bool(attrs.get("replied", i % 7 == 0)),
                    reply_hours=float(attrs["reply_hours"]) if attrs.get("reply_hours") is not None else (12.0 if i % 7 == 0 else None),
                    reply_text=str(attrs.get("reply_text") or ("interested let's meet" if i % 7 == 0 else "")),
                    meeting_booked=bool(attrs.get("meeting_booked", i % 11 == 0)),
                    proposal_sent=bool(attrs.get("proposal_sent", i % 13 == 0)),
                    closed_won=bool(attrs.get("closed_won", i % 17 == 0)),
                    closed_lost=bool(attrs.get("closed_lost", i % 19 == 0)),
                    deal_value=float(attrs.get("deal_value") or (25000 if i % 17 == 0 else 0)),
                    followup_number=int(attrs.get("followup_number") or (i % 4)),
                    sequence_length=int(attrs.get("sequence_length") or 3),
                    delay_days=float(attrs.get("delay_days") or 3.0),
                    timezone=str(attrs.get("timezone") or "UTC"),
                    founder_actor=True,
                    pain_points=list(attrs.get("pain_points") or []),
                    technology=list(attrs.get("technology") or []),
                    buyer_persona=str(attrs.get("buyer_persona") or "") or None,
                    evidence=[f"company:{company.id}", "compose:goap_aip"],
                )
            )
        assets = list((companies[0].attributes or {}).get("portfolio_assets") or []) if companies else []
        return ROIPInput(events=events, previous_period_events=events[: max(1, len(events) // 2)], portfolio_assets=assets)

    async def store_decision(self, decision: ROIPDecision) -> dict[str, Any]:
        self.session.add(
            ROIPEmailMetricsRow(
                payload=decision.email_metrics.model_dump(mode="json"),
                evidence=list(decision.email_metrics.evidence),
                confidence=decision.email_metrics.confidence,
            )
        )
        for s in decision.subjects[:50]:
            self.session.add(
                ROIPSubjectPerformanceRow(
                    subject=s.subject[:500],
                    rank=s.rank,
                    payload=s.model_dump(mode="json"),
                    evidence=list(s.evidence),
                )
            )
        for c in decision.ctas[:50]:
            self.session.add(
                ROIPCTAPerformanceRow(cta=c.cta, score=c.score, payload=c.model_dump(mode="json"), evidence=list(c.evidence))
            )
        self.session.add(
            ROIPFollowupPatternRow(
                payload=decision.followup.model_dump(mode="json"),
                evidence=list(decision.followup.evidence),
                confidence=decision.followup.confidence,
            )
        )
        for i in decision.industries[:50]:
            self.session.add(
                ROIPIndustryMetricsRow(
                    industry=i.industry, rank=i.rank, payload=i.model_dump(mode="json"), evidence=list(i.evidence)
                )
            )
        self.session.add(
            ROIPFounderMetricsRow(
                payload=decision.founder.model_dump(mode="json"),
                evidence=list(decision.founder.evidence),
                revenue=decision.founder.revenue,
            )
        )
        for o in decision.offers[:50]:
            self.session.add(
                ROIPOfferMetricsRow(offer=o.offer, score=o.score, payload=o.model_dump(mode="json"), evidence=list(o.evidence))
            )
        for a in decision.case_studies[:50]:
            self.session.add(
                ROIPCaseStudyMetricsRow(
                    asset_id=a.asset_id, score=a.score, payload=a.model_dump(mode="json"), evidence=list(a.evidence)
                )
            )
        for r in decision.replies[:200]:
            self.session.add(
                ROIPReplyAnalysisRow(
                    reply_id=r.reply_id,
                    category=r.category.value,
                    payload=r.model_dump(mode="json"),
                    evidence=list(r.evidence),
                )
            )
        self.session.add(
            ROIPLearningEventRow(
                insight_type=decision.learning.insight_type,
                modifies_production=False,
                payload=decision.learning.model_dump(mode="json"),
                evidence=list(decision.learning.evidence),
            )
        )
        for b in decision.benchmarks:
            self.session.add(
                ROIPRevenueBenchmarkRow(period=b.period.value, payload=b.model_dump(mode="json"), evidence=list(b.evidence))
            )
        for rec in decision.recommendations:
            self.session.add(
                ROIPRecommendationRow(
                    recommendation_id=rec.recommendation_id,
                    title=rec.title,
                    requires_founder_approval=True,
                    modifies_production=False,
                    payload=rec.model_dump(mode="json"),
                    evidence=list(rec.evidence),
                )
            )
        await self.session.flush()
        return {"stored": True, "recommendations": len(decision.recommendations)}

    async def latest_email(self) -> ROIPEmailMetricsRow | None:
        return await self.session.scalar(select(ROIPEmailMetricsRow).order_by(ROIPEmailMetricsRow.created_at.desc()).limit(1))

    async def recent_recommendations(self, *, limit: int = 50) -> list[ROIPRecommendationRow]:
        return list(
            (
                await self.session.execute(
                    select(ROIPRecommendationRow).order_by(ROIPRecommendationRow.created_at.desc()).limit(limit)
                )
            )
            .scalars()
            .all()
        )

    async def recent_industries(self, *, limit: int = 50) -> list[ROIPIndustryMetricsRow]:
        return list(
            (
                await self.session.execute(
                    select(ROIPIndustryMetricsRow).order_by(ROIPIndustryMetricsRow.created_at.desc()).limit(limit)
                )
            )
            .scalars()
            .all()
        )

    async def recent_offers(self, *, limit: int = 50) -> list[ROIPOfferMetricsRow]:
        return list(
            (await self.session.execute(select(ROIPOfferMetricsRow).order_by(ROIPOfferMetricsRow.created_at.desc()).limit(limit)))
            .scalars()
            .all()
        )

    async def recent_benchmarks(self, *, limit: int = 20) -> list[ROIPRevenueBenchmarkRow]:
        return list(
            (
                await self.session.execute(
                    select(ROIPRevenueBenchmarkRow).order_by(ROIPRevenueBenchmarkRow.created_at.desc()).limit(limit)
                )
            )
            .scalars()
            .all()
        )

    async def latest_learning(self) -> ROIPLearningEventRow | None:
        return await self.session.scalar(select(ROIPLearningEventRow).order_by(ROIPLearningEventRow.created_at.desc()).limit(1))

    async def recent_replies(self, *, limit: int = 100) -> list[ROIPReplyAnalysisRow]:
        return list(
            (
                await self.session.execute(
                    select(ROIPReplyAnalysisRow).order_by(ROIPReplyAnalysisRow.created_at.desc()).limit(limit)
                )
            )
            .scalars()
            .all()
        )

    async def latest_founder(self) -> ROIPFounderMetricsRow | None:
        return await self.session.scalar(select(ROIPFounderMetricsRow).order_by(ROIPFounderMetricsRow.created_at.desc()).limit(1))
