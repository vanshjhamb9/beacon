from __future__ import annotations

import uuid
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.intelligence import Company
from app.models.revenue_execution_validation import (
    RevAcceptanceGateRow,
    RevConnectorScoreRow,
    RevDailyReportRow,
    RevEvaluationRow,
    RevFounderQueueCardRow,
    RevFunnelSnapshotRow,
    RevManualQaRow,
    RevRejectionRecordRow,
)
from app.models.raw_event import RawEvent
from revenue_execution_validation import (
    CAMPAIGN_EXECUTION_ENABLED,
    GMAIL_PRODUCTION_ENABLED,
    LIVE_OUTREACH_ENABLED,
    PRODUCTION_SEND_LOCKED,
    WHATSAPP_PRODUCTION_ENABLED,
)
from revenue_execution_validation.founder_queue_v3.engine import FounderQueueV3Engine
from revenue_execution_validation.manual_qa.engine import ManualQaWorkspaceEngine
from revenue_execution_validation.pipelines.engine import RevenueExecutionPipeline
from revenue_execution_validation.rebuild.engine import RevRebuildEngine


class RevenueExecutionValidationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.pipeline = RevenueExecutionPipeline()
        self.rebuild_engine = RevRebuildEngine()
        self.qa_engine = ManualQaWorkspaceEngine()
        self.queue_engine = FounderQueueV3Engine()

    def evaluate(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.pipeline.evaluate(payload).model_dump(mode="json")

    async def reality_funnel(self) -> dict[str, Any]:
        report = await self._latest_or_rebuild()
        return report.get("funnel") or {}

    async def rejections(self) -> dict[str, Any]:
        from revenue_execution_validation.rejection.engine import RejectionAnalysisEngine
        from revenue_execution_validation.models.types import RevSnapshot

        snaps = await self._load_snapshots()
        return RejectionAnalysisEngine().analyze(snaps)

    async def connector_scoreboard(self) -> dict[str, Any]:
        report = await self._latest_or_rebuild()
        return {"items": report.get("connector_scores") or [], "scoring_version": "rev-v1"}

    async def founder_queue_v3(self) -> dict[str, Any]:
        snaps = await self._load_snapshots()
        cards = self.queue_engine.build(snaps)
        return {"items": [c.model_dump(mode="json") for c in cards], "count": len(cards), "max": 10}

    async def qa_pending(self) -> dict[str, Any]:
        snaps = await self._load_snapshots()
        return {"items": self.qa_engine.queue(snaps), "ratings": [r.value for r in self.qa_engine.RATINGS]}

    async def qa_submit(self, *, company_id: str | None, company_name: str | None, rating: str, reviewer: str = "founder", notes: str | None = None) -> dict[str, Any]:
        row = RevManualQaRow(
            id=uuid.uuid4(),
            company_id=UUID(company_id) if company_id else None,
            company_name=company_name,
            rating=rating,
            reviewer=reviewer,
            notes=notes,
            payload={"rating": rating, "reviewer": reviewer},
        )
        self.session.add(row)
        await self.session.commit()
        return {"status": "recorded", "rating": rating, "note": "Analytics only — rules unchanged"}

    async def qa_analytics(self) -> dict[str, Any]:
        rows = list((await self.session.scalars(select(RevManualQaRow).where(RevManualQaRow.deleted_at.is_(None)).limit(2000))).all())
        decisions = [{"rating": r.rating} for r in rows]
        return self.qa_engine.analytics(decisions)

    async def daily_report(self) -> dict[str, Any]:
        report = await self.rebuild(persist=True)
        return report.get("daily") or {}

    async def acceptance(self) -> dict[str, Any]:
        report = await self._latest_or_rebuild()
        gate = report.get("acceptance") or {}
        flags = {
            "LIVE_OUTREACH_ENABLED": bool(gate.get("production_unlocked")) and LIVE_OUTREACH_ENABLED,
            "PRODUCTION_SEND_LOCKED": not bool(gate.get("production_unlocked")) or PRODUCTION_SEND_LOCKED,
            "GMAIL_PRODUCTION_ENABLED": bool(gate.get("gmail_enabled")) and GMAIL_PRODUCTION_ENABLED,
            "WHATSAPP_PRODUCTION_ENABLED": bool(gate.get("whatsapp_enabled")) and WHATSAPP_PRODUCTION_ENABLED,
            "CAMPAIGN_EXECUTION_ENABLED": bool(gate.get("campaigns_enabled")) and CAMPAIGN_EXECUTION_ENABLED,
        }
        # Package defaults keep production disabled even if gates pass until explicit unlock constant flip
        if PRODUCTION_SEND_LOCKED or not LIVE_OUTREACH_ENABLED:
            flags["LIVE_OUTREACH_ENABLED"] = False
            flags["GMAIL_PRODUCTION_ENABLED"] = False
            flags["WHATSAPP_PRODUCTION_ENABLED"] = False
            flags["CAMPAIGN_EXECUTION_ENABLED"] = False
            flags["PRODUCTION_SEND_LOCKED"] = True
        return {**gate, "outreach_flags": flags, "scoring_version": "rev-v1"}

    async def dashboard(self) -> dict[str, Any]:
        report = await self._latest_or_rebuild()
        acceptance = await self.acceptance()
        return {
            "funnel": report.get("funnel"),
            "connector_scores": report.get("connector_scores"),
            "rejection_top": report.get("rejection_top"),
            "founder_queue": (await self.founder_queue_v3()).get("items"),
            "daily": report.get("daily"),
            "acceptance": acceptance,
            "scoring_version": "rev-v1",
        }

    async def rebuild(self, *, persist: bool = True, limit: int = 500) -> dict[str, Any]:
        companies = list(
            (await self.session.scalars(select(Company).where(Company.deleted_at.is_(None)).order_by(Company.updated_at.desc()).limit(limit))).all()
        )
        from sqlalchemy import func

        signals_collected = int((await self.session.scalar(select(func.count()).select_from(RawEvent))) or 0)

        snaps = []
        for company in companies:
            attrs = dict(company.attributes or {})
            payload = {
                "company_id": str(company.id),
                "company_name": company.name,
                "website": attrs.get("official_website") or (f"https://{company.primary_domain}" if company.primary_domain else None),
                "official_website": attrs.get("official_website"),
                "domain": company.primary_domain,
                "description": company.description,
                "industry": company.industry or attrs.get("industry"),
                "country": attrs.get("country") or (attrs.get("cir_founder_card") or {}).get("country"),
                "source": attrs.get("source") or "unknown",
                "erowd_admitted": bool(attrs.get("erowd_verified") or attrs.get("erowd_admitted")),
                "erowd_verified": bool(attrs.get("erowd_verified")),
                "attributes": attrs,
                "cir_founder_card": attrs.get("cir_founder_card") or {},
                "cir_narrative": attrs.get("cir_narrative") or {},
                "cir_classification": attrs.get("cir_classification"),
                "buying_signals": attrs.get("cir_buying_signals") or [],
                "best_service": attrs.get("cir_best_service"),
                "business_email": (attrs.get("cir_founder_card") or {}).get("business_email"),
                "decision_maker": ((attrs.get("cir_founder_card") or {}).get("decision_makers") or [None])[0],
                "confidence": attrs.get("cir_readiness_score") or 0,
                "why_now": (attrs.get("cir_narrative") or {}).get("why_now"),
                "opportunity": (attrs.get("cir_narrative") or {}).get("what_opportunity"),
            }
            snap = self.pipeline.evaluate(payload)
            snaps.append(snap)

        qa = await self.qa_analytics()
        report = self.rebuild_engine.build(
            snaps,
            signals_collected=signals_collected or len(snaps),
            qa_accuracy=float(qa.get("accuracy_pct") or 0),
            qa_sample_size=int(qa.get("total") or 0),
        )
        out = report.model_dump(mode="json")
        if persist:
            await self._persist_report(out, snaps)
        return out

    async def _persist_report(self, report: dict[str, Any], snaps) -> None:
        funnel = report.get("funnel") or {}
        self.session.add(
            RevFunnelSnapshotRow(
                id=uuid.uuid4(),
                payload=funnel,
                revenue_ready=int(funnel.get("revenue_ready") or 0),
                founder_queue=int(funnel.get("founder_queue") or 0),
            )
        )
        for score in report.get("connector_scores") or []:
            self.session.add(
                RevConnectorScoreRow(
                    id=uuid.uuid4(),
                    connector=str(score.get("connector") or "unknown"),
                    grade=str(score.get("grade") or "Weak"),
                    revenue_ready_pct=float(score.get("revenue_ready_pct") or 0),
                    payload=score,
                )
            )
        for rank, card in enumerate(report.get("daily", {}).get("top_5_opportunities") or [], start=1):
            pass
        fq = await self.founder_queue_v3()
        for rank, card in enumerate(fq.get("items") or [], start=1):
            self.session.add(
                RevFounderQueueCardRow(
                    id=uuid.uuid4(),
                    company_id=UUID(card["company_id"]) if card.get("company_id") and len(str(card["company_id"])) == 36 else None,
                    company_name=str(card.get("company") or ""),
                    rank=rank,
                    payload=card,
                )
            )
        daily = report.get("daily") or {}
        self.session.add(
            RevDailyReportRow(
                id=uuid.uuid4(),
                payload=daily,
                revenue_ready=int(daily.get("revenue_ready") or 0),
            )
        )
        gate = report.get("acceptance") or {}
        self.session.add(
            RevAcceptanceGateRow(
                id=uuid.uuid4(),
                production_unlocked=bool(gate.get("production_unlocked")),
                failures=list(gate.get("failures") or []),
                payload=gate,
            )
        )
        for snap in snaps:
            data = snap.model_dump(mode="json")
            cid = None
            try:
                cid = UUID(snap.company_id)
            except Exception:  # noqa: BLE001
                cid = None
            self.session.add(
                RevEvaluationRow(
                    id=uuid.uuid4(),
                    company_id=cid,
                    company_name=snap.company_name,
                    source=snap.source,
                    is_revenue_ready=snap.check.is_revenue_ready,
                    confidence=snap.check.confidence,
                    payload=data,
                    evidence=list(snap.evidence),
                )
            )
            if not snap.check.is_revenue_ready:
                self.session.add(
                    RevRejectionRecordRow(
                        id=uuid.uuid4(),
                        company_id=cid,
                        company_name=snap.company_name,
                        source=snap.source,
                        industry=snap.check.industry,
                        reasons=[r.value for r in snap.rejection_reasons],
                        payload=data,
                    )
                )
        await self.session.commit()

    async def _load_snapshots(self):
        from revenue_execution_validation.models.types import RevSnapshot

        rows = list(
            (
                await self.session.scalars(
                    select(RevEvaluationRow)
                    .where(RevEvaluationRow.deleted_at.is_(None))
                    .order_by(RevEvaluationRow.created_at.desc())
                    .limit(2000)
                )
            ).all()
        )
        snaps = []
        for r in rows:
            try:
                snaps.append(RevSnapshot.model_validate(r.payload))
            except Exception:  # noqa: BLE001
                continue
        if snaps:
            return snaps
        # Fallback: rebuild without persist
        report_snaps = []
        companies = list((await self.session.scalars(select(Company).where(Company.deleted_at.is_(None)).limit(200))).all())
        for company in companies:
            attrs = dict(company.attributes or {})
            report_snaps.append(
                self.pipeline.evaluate(
                    {
                        "company_id": str(company.id),
                        "company_name": company.name,
                        "website": attrs.get("official_website"),
                        "domain": company.primary_domain,
                        "description": company.description,
                        "industry": company.industry,
                        "erowd_admitted": bool(attrs.get("erowd_verified")),
                        "attributes": attrs,
                        "source": attrs.get("source") or "unknown",
                        "cir_founder_card": attrs.get("cir_founder_card") or {},
                        "cir_narrative": attrs.get("cir_narrative") or {},
                    }
                )
            )
        return report_snaps

    async def _latest_or_rebuild(self) -> dict[str, Any]:
        row = await self.session.scalar(
            select(RevFunnelSnapshotRow).where(RevFunnelSnapshotRow.deleted_at.is_(None)).order_by(RevFunnelSnapshotRow.created_at.desc()).limit(1)
        )
        if row and row.payload:
            gate = await self.session.scalar(
                select(RevAcceptanceGateRow).where(RevAcceptanceGateRow.deleted_at.is_(None)).order_by(RevAcceptanceGateRow.created_at.desc()).limit(1)
            )
            daily = await self.session.scalar(
                select(RevDailyReportRow).where(RevDailyReportRow.deleted_at.is_(None)).order_by(RevDailyReportRow.created_at.desc()).limit(1)
            )
            scores = list(
                (
                    await self.session.scalars(
                        select(RevConnectorScoreRow).where(RevConnectorScoreRow.deleted_at.is_(None)).order_by(RevConnectorScoreRow.created_at.desc()).limit(40)
                    )
                ).all()
            )
            return {
                "funnel": row.payload,
                "acceptance": (gate.payload if gate else {}),
                "daily": (daily.payload if daily else {}),
                "connector_scores": [s.payload for s in scores],
                "rejection_top": [],
            }
        return await self.rebuild(persist=True)
