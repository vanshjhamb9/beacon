from __future__ import annotations

import uuid
from typing import Any
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company_intelligence import (
    CirBusinessProfileRow,
    CirBuyingSignalRow,
    CirCompanyProfileRow,
    CirOpportunityNarrativeRow,
    CirProductProfileRow,
    CirRevenueReadinessRow,
    CirServiceMatchRow,
    CirTechnologyProfileRow,
)
from app.models.intelligence import Company
from company_intelligence.founder_queue.engine import CirFounderQueueEngine
from company_intelligence.pipelines.engine import CirPipeline
from company_intelligence.rebuild.engine import CirRebuildEngine


class CompanyIntelligenceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.pipeline = CirPipeline()
        self.rebuild_engine = CirRebuildEngine()
        self.queue_engine = CirFounderQueueEngine()

    def evaluate(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.pipeline.evaluate(payload).model_dump(mode="json")

    async def persist(self, snap: dict[str, Any], *, company_id: UUID) -> UUID:
        profile_id = uuid.uuid4()
        readiness = snap.get("readiness") or {}
        business = snap.get("business") or {}
        card = snap.get("founder_card") or {}
        self.session.add(
            CirCompanyProfileRow(
                id=profile_id,
                company_id=company_id,
                company_name=str(snap.get("company_name") or ""),
                website=snap.get("website"),
                domain=snap.get("domain"),
                verdict=str(snap.get("verdict") or "REJECTED"),
                erowd_admitted=bool(snap.get("erowd_admitted")),
                founder_queue_eligible=bool(snap.get("founder_queue_eligible")),
                payload=snap,
                evidence=list(snap.get("evidence") or []),
                scoring_version="cir-v1",
            )
        )
        self.session.add(
            CirBusinessProfileRow(
                id=uuid.uuid4(),
                company_id=company_id,
                industry=(business.get("industry") or {}).get("value"),
                primary_product=(business.get("primary_product") or {}).get("value"),
                country=(business.get("country") or {}).get("value"),
                payload=business,
                evidence=list(business.get("evidence") or []),
            )
        )
        self.session.add(
            CirProductProfileRow(
                id=uuid.uuid4(),
                company_id=company_id,
                payload=snap.get("products") or {},
                evidence=list((snap.get("products") or {}).get("evidence") or []),
            )
        )
        techs = snap.get("technologies") or []
        self.session.add(
            CirTechnologyProfileRow(
                id=uuid.uuid4(),
                company_id=company_id,
                technologies=techs,
                payload={"technologies": techs},
                evidence=[t.get("technology") for t in techs if isinstance(t, dict)][:20],
            )
        )
        signals = snap.get("buying_signals") or []
        self.session.add(
            CirBuyingSignalRow(
                id=uuid.uuid4(),
                company_id=company_id,
                signals=signals,
                payload={"signals": signals},
                evidence=[s.get("signal_type") for s in signals if isinstance(s, dict)][:20],
            )
        )
        matches = snap.get("service_matches") or []
        self.session.add(
            CirServiceMatchRow(
                id=uuid.uuid4(),
                company_id=company_id,
                best_service=(matches[0].get("service") if matches else None),
                matches=matches,
                payload={"matches": matches},
                evidence=[m.get("service") for m in matches if isinstance(m, dict)][:12],
            )
        )
        self.session.add(
            CirRevenueReadinessRow(
                id=uuid.uuid4(),
                company_id=company_id,
                total=float(readiness.get("total") or 0),
                classification=str(readiness.get("classification") or "Rejected"),
                founder_queue_eligible=bool(snap.get("founder_queue_eligible")),
                breakdown=readiness.get("breakdown") or {},
                payload=readiness,
                evidence=list(readiness.get("evidence") or []),
                scoring_version="cir-v1",
            )
        )
        narrative = snap.get("narrative") or {}
        self.session.add(
            CirOpportunityNarrativeRow(
                id=uuid.uuid4(),
                company_id=company_id,
                best_service=narrative.get("which_service"),
                payload=narrative,
                evidence=list(narrative.get("evidence") or []),
            )
        )
        company = await self.session.get(Company, company_id)
        if company is not None:
            attrs = dict(company.attributes or {})
            attrs.update(
                {
                    "cir_verified": True,
                    "cir_classification": readiness.get("classification"),
                    "cir_readiness_score": readiness.get("total"),
                    "cir_best_service": card.get("best_service"),
                    "cir_founder_queue_eligible": bool(snap.get("founder_queue_eligible")),
                    "cir_buying_signals": [s.get("signal_type") for s in signals if isinstance(s, dict)][:8],
                    "cir_technologies": [t.get("technology") for t in techs if isinstance(t, dict)][:12],
                    "cir_narrative": narrative,
                    "cir_founder_card": card,
                }
            )
            company.attributes = attrs
        await self.session.flush()
        return profile_id

    async def company_card(self, company_id: UUID) -> dict[str, Any] | None:
        row = await self.session.scalar(
            select(CirCompanyProfileRow)
            .where(CirCompanyProfileRow.deleted_at.is_(None), CirCompanyProfileRow.company_id == company_id)
            .order_by(CirCompanyProfileRow.created_at.desc())
            .limit(1)
        )
        if not row:
            company = await self.session.get(Company, company_id)
            if not company:
                return None
            attrs = company.attributes or {}
            return {
                "company_id": str(company_id),
                "founder_card": attrs.get("cir_founder_card") or {},
                "status": "not_reconstructed",
            }
        return {
            "company_id": str(company_id),
            "snapshot": row.payload,
            "founder_card": (row.payload or {}).get("founder_card") or {},
            "readiness": (row.payload or {}).get("readiness") or {},
            "founder_queue_eligible": row.founder_queue_eligible,
            "status": "ok",
        }

    async def dashboard(self) -> dict[str, Any]:
        rows = list(
            (
                await self.session.scalars(
                    select(CirCompanyProfileRow)
                    .where(CirCompanyProfileRow.deleted_at.is_(None))
                    .order_by(CirCompanyProfileRow.created_at.desc())
                    .limit(100)
                )
            ).all()
        )
        items = []
        for r in rows:
            p = r.payload or {}
            card = p.get("founder_card") or {}
            readiness = p.get("readiness") or {}
            items.append(
                {
                    "company": r.company_name,
                    "website": r.website,
                    "industry": card.get("industry"),
                    "revenue_readiness": readiness.get("classification") or card.get("revenue_readiness"),
                    "readiness_score": readiness.get("total") or card.get("readiness_score"),
                    "technology": ", ".join((card.get("buying_signals") and []) or [t.get("technology") for t in (p.get("technologies") or [])[:3] if isinstance(t, dict)]),
                    "buying_signals": ", ".join(card.get("buying_signals") or []),
                    "decision_makers": ", ".join(card.get("decision_makers") or []),
                    "business_email": card.get("business_email"),
                    "best_service": card.get("best_service"),
                    "next_action": card.get("recommended_action"),
                    "evidence": len(p.get("evidence") or []),
                    "founder_queue_eligible": r.founder_queue_eligible,
                }
            )
        # Fix technology column
        for i, r in enumerate(rows):
            techs = (r.payload or {}).get("technologies") or []
            items[i]["technology"] = ", ".join(t.get("technology") for t in techs[:4] if isinstance(t, dict)) or "UNKNOWN"
        return {
            "items": items,
            "founder_queue": sum(1 for r in rows if r.founder_queue_eligible),
            "scoring_version": "cir-v1",
        }

    async def search(self, q: str, *, limit: int = 40) -> dict[str, Any]:
        pattern = f"%{q.lower()}%"
        rows = list(
            (
                await self.session.scalars(
                    select(CirCompanyProfileRow)
                    .where(
                        CirCompanyProfileRow.deleted_at.is_(None),
                        or_(
                            CirCompanyProfileRow.company_name.ilike(pattern),
                            CirCompanyProfileRow.domain.ilike(pattern),
                        ),
                    )
                    .order_by(CirCompanyProfileRow.created_at.desc())
                    .limit(limit)
                )
            ).all()
        )
        return {
            "items": [
                {
                    "company": r.company_name,
                    "website": r.website,
                    "domain": r.domain,
                    "verdict": r.verdict,
                    "founder_queue_eligible": r.founder_queue_eligible,
                }
                for r in rows
            ]
        }

    async def opportunities(self) -> dict[str, Any]:
        rows = list(
            (
                await self.session.scalars(
                    select(CirCompanyProfileRow)
                    .where(
                        CirCompanyProfileRow.deleted_at.is_(None),
                        CirCompanyProfileRow.founder_queue_eligible.is_(True),
                    )
                    .order_by(CirCompanyProfileRow.created_at.desc())
                    .limit(100)
                )
            ).all()
        )
        from company_intelligence.models.types import CirSnapshot

        snaps = []
        for r in rows:
            try:
                snaps.append(CirSnapshot.model_validate(r.payload))
            except Exception:  # noqa: BLE001
                continue
        cards = self.queue_engine.build(snaps)
        return {"items": [c.model_dump(mode="json") for c in cards], "count": len(cards)}

    async def summary(self) -> dict[str, Any]:
        return await self.report()

    async def report(self) -> dict[str, Any]:
        rows = list(
            (await self.session.scalars(select(CirCompanyProfileRow).where(CirCompanyProfileRow.deleted_at.is_(None)).limit(2000))).all()
        )
        from company_intelligence.models.types import CirSnapshot

        snaps = []
        for r in rows:
            try:
                snaps.append(CirSnapshot.model_validate(r.payload))
            except Exception:  # noqa: BLE001
                continue
        if not snaps:
            return {"status": "empty", "total_companies": 0}
        return self.rebuild_engine.build(snaps).model_dump(mode="json")

    async def rebuild(self, *, limit: int = 500, fetch_website: bool = False) -> dict[str, Any]:
        companies = list(
            (
                await self.session.scalars(
                    select(Company)
                    .where(Company.deleted_at.is_(None))
                    .order_by(Company.updated_at.desc())
                    .limit(limit)
                )
            ).all()
        )
        snaps = []
        processed = 0
        for company in companies:
            attrs = dict(company.attributes or {})
            if not (attrs.get("erowd_verified") or attrs.get("erowd_admitted")):
                continue
            payload = {
                "company_id": str(company.id),
                "company_name": company.name,
                "website": attrs.get("official_website") or (f"https://{company.primary_domain}" if company.primary_domain else None),
                "official_website": attrs.get("official_website"),
                "domain": company.primary_domain,
                "description": company.description,
                "industry": company.industry or attrs.get("industry"),
                "erowd_admitted": True,
                "erowd_verified": True,
                "attributes": attrs,
                "fetch_website": fetch_website,
                "website_pages": attrs.get("website_pages") or attrs.get("cir_website_pages"),
                "decision_makers": attrs.get("decision_makers") or [],
                "technologies": attrs.get("technologies") or attrs.get("cir_technologies") or [],
                "buying_signals": attrs.get("buying_signals") or [],
                "content": attrs.get("narrative") or company.description or "",
            }
            snap = self.pipeline.evaluate(payload)
            snaps.append(snap)
            await self.persist(snap.model_dump(mode="json"), company_id=company.id)
            processed += 1
        await self.session.commit()
        report = self.rebuild_engine.build(snaps)
        out = report.model_dump(mode="json")
        out["processed"] = processed
        return out

    async def process_verified(self, *, limit: int = 40) -> dict[str, Any]:
        """Worker entry — only EROWD-admitted companies without recent CIR."""
        companies = list(
            (
                await self.session.scalars(
                    select(Company).where(Company.deleted_at.is_(None)).order_by(Company.updated_at.desc()).limit(limit * 3)
                )
            ).all()
        )
        done = 0
        for company in companies:
            if done >= limit:
                break
            attrs = company.attributes or {}
            if not (attrs.get("erowd_verified") or attrs.get("erowd_admitted")):
                continue
            if attrs.get("cir_verified") and attrs.get("cir_classification"):
                continue
            payload = {
                "company_id": str(company.id),
                "company_name": company.name,
                "website": attrs.get("official_website") or (f"https://{company.primary_domain}" if company.primary_domain else None),
                "official_website": attrs.get("official_website"),
                "domain": company.primary_domain,
                "description": company.description,
                "industry": company.industry,
                "erowd_admitted": True,
                "content": company.description or "",
                "website_pages": attrs.get("website_pages"),
                "decision_makers": attrs.get("decision_makers") or [],
            }
            snap = self.pipeline.evaluate(payload)
            await self.persist(snap.model_dump(mode="json"), company_id=company.id)
            done += 1
        await self.session.commit()
        return {"processed": done, "scoring_version": "cir-v1"}
