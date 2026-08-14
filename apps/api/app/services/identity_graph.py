from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity_graph import (
    IgfCanonicalCompany,
    IgfFunnelSnapshot,
    IgfIdentityCandidate,
    IgfIdentityEvidence,
    IgfResolutionRun,
)
from app.models.intelligence import Company
from app.models.raw_event import RawEvent
from identity_graph.pipelines.engine import IdentityResolutionPipeline
from identity_graph.rebuild.engine import IgfRebuildEngine
from intelligence.entity_resolution.normalization import normalize_company_name


def _norm_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (name or "").lower()) or "unknown"


class IdentityGraphService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.pipeline = IdentityResolutionPipeline()
        self.rebuild_engine = IgfRebuildEngine()

    def evaluate_signal(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.pipeline.evaluate(payload).model_dump(mode="json")

    async def _existing_canonical(self) -> list[dict[str, Any]]:
        rows = (
            await self.session.execute(
                select(IgfCanonicalCompany).where(
                    IgfCanonicalCompany.deleted_at.is_(None),
                    IgfCanonicalCompany.status.in_(["ACTIVE", "MERGED"]),
                )
            )
        ).scalars().all()
        return [
            {
                "id": str(r.id),
                "official_domain": r.official_domain,
                "trade_name": r.trade_name,
                "legal_name": r.legal_name,
                "aliases": r.aliases or [],
            }
            for r in rows
        ]

    async def persist_run(
        self,
        snap: dict[str, Any],
        *,
        raw_event_id: UUID | None = None,
        company_id: UUID | None = None,
        commit: bool = False,
    ) -> UUID:
        run_id = uuid.uuid4()
        admission = snap.get("admission") or {}
        candidate = snap.get("candidate") or {}
        self.session.add(
            IgfResolutionRun(
                id=run_id,
                signal_id=str(snap.get("signal_id") or ""),
                raw_event_id=raw_event_id,
                source=str(snap.get("source") or ""),
                source_role=str(snap.get("source_role") or ""),
                verdict=str(admission.get("verdict") or "REJECTED"),
                admitted=bool(admission.get("admitted")),
                identity_score=float((snap.get("score") or {}).get("score") or 0),
                domain=snap.get("domain"),
                website=snap.get("website"),
                payload=snap,
                evidence=list(admission.get("evidence") or []),
                scoring_version="igf-v1",
            )
        )
        await self.session.flush()
        self.session.add(
            IgfIdentityCandidate(
                id=uuid.uuid4(),
                run_id=run_id,
                signal_id=str(snap.get("signal_id") or ""),
                name=str(candidate.get("name") or "unknown"),
                normalized_key=_norm_key(str(candidate.get("name") or "")),
                aliases=list(candidate.get("aliases") or []),
                possible_domain=candidate.get("possible_domain"),
                source=str(candidate.get("source") or snap.get("source") or ""),
                source_role=str(candidate.get("source_role") or snap.get("source_role") or ""),
                confidence=float(candidate.get("confidence") or 0),
                payload=candidate,
                evidence=list(candidate.get("evidence") or []),
            )
        )
        canonical_id: UUID | None = None
        canonical = snap.get("canonical")
        if admission.get("admitted") and canonical and snap.get("domain"):
            existing = (
                await self.session.execute(
                    select(IgfCanonicalCompany).where(
                        IgfCanonicalCompany.deleted_at.is_(None),
                        IgfCanonicalCompany.official_domain == str(snap["domain"]),
                    )
                )
            ).scalar_one_or_none()
            if existing:
                canonical_id = existing.id
                existing.last_seen = datetime.now(UTC)
                existing.signals = list(dict.fromkeys([*(existing.signals or []), str(snap.get("signal_id") or "")]))
                if company_id and not existing.company_id:
                    existing.company_id = company_id
            else:
                canonical_id = uuid.uuid4()
                self.session.add(
                    IgfCanonicalCompany(
                        id=canonical_id,
                        company_id=company_id,
                        legal_name=str(canonical.get("legal_name") or candidate.get("name") or "unknown"),
                        trade_name=str(canonical.get("trade_name") or candidate.get("name") or "unknown"),
                        normalized_key=_norm_key(str(canonical.get("trade_name") or candidate.get("name") or "")),
                        aliases=list(canonical.get("aliases") or []),
                        official_domain=snap.get("domain"),
                        website=snap.get("website"),
                        linkedin_company_url=canonical.get("linkedin_company_url"),
                        github_organization=canonical.get("github_organization"),
                        crunchbase=canonical.get("crunchbase"),
                        industry=canonical.get("industry"),
                        country=canonical.get("country"),
                        description=canonical.get("description"),
                        confidence=float(canonical.get("confidence") or 0),
                        status="ACTIVE",
                        verified_at=datetime.now(UTC),
                        last_seen=datetime.now(UTC),
                        collectors=list(canonical.get("collectors") or [snap.get("source")]),
                        signals=[str(snap.get("signal_id") or "")],
                        payload=canonical,
                        evidence=list(snap.get("evidence_items") or []),
                        scoring_version="igf-v1",
                    )
                )

        for ev in snap.get("evidence_items") or []:
            self.session.add(
                IgfIdentityEvidence(
                    id=uuid.uuid4(),
                    run_id=run_id,
                    canonical_id=canonical_id,
                    source=str(ev.get("source") or ""),
                    field=str(ev.get("field") or ""),
                    value=str(ev.get("value") or ""),
                    confidence=float(ev.get("confidence") or 0),
                    collector=str(ev.get("collector") or "unknown"),
                    verified=bool(ev.get("verified")),
                    reason=ev.get("reason"),
                    payload=ev,
                    evidence=list(ev.get("evidence") or []),
                )
            )

        if commit:
            await self.session.commit()
        return run_id

    async def dashboard(self) -> dict[str, Any]:
        latest = (
            await self.session.execute(
                select(IgfFunnelSnapshot)
                .where(IgfFunnelSnapshot.deleted_at.is_(None))
                .order_by(IgfFunnelSnapshot.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        active = (
            await self.session.execute(
                select(func.count()).select_from(IgfCanonicalCompany).where(
                    IgfCanonicalCompany.deleted_at.is_(None),
                    IgfCanonicalCompany.status == "ACTIVE",
                )
            )
        ).scalar() or 0
        pending = (
            await self.session.execute(
                select(func.count()).select_from(IgfCanonicalCompany).where(
                    IgfCanonicalCompany.deleted_at.is_(None),
                    IgfCanonicalCompany.status == "PENDING",
                )
            )
        ).scalar() or 0
        payload = dict(latest.payload) if latest else {}
        return {
            "scoring_version": "igf-v1",
            "active_canonical": int(active),
            "pending_canonical": int(pending),
            "funnel": payload,
            "signals": latest.signals if latest else 0,
            "candidates": latest.candidates if latest else 0,
            "official_websites": latest.official_websites if latest else 0,
            "verified_companies": latest.verified_companies if latest else int(active),
            "top_sources": payload.get("top_sources") or {},
            "top_failures": payload.get("top_failures") or {},
            "identity_precision": payload.get("identity_precision") or 0,
            "revenue_ready_downstream": payload.get("revenue_ready") or 0,
        }

    async def report(self) -> dict[str, Any]:
        return await self.dashboard()

    async def search(self, q: str, *, limit: int = 40) -> dict[str, Any]:
        pattern = f"%{q.strip()}%"
        rows = (
            await self.session.execute(
                select(IgfCanonicalCompany)
                .where(
                    IgfCanonicalCompany.deleted_at.is_(None),
                    or_(
                        IgfCanonicalCompany.trade_name.ilike(pattern),
                        IgfCanonicalCompany.legal_name.ilike(pattern),
                        IgfCanonicalCompany.official_domain.ilike(pattern),
                    ),
                )
                .order_by(IgfCanonicalCompany.confidence.desc())
                .limit(limit)
            )
        ).scalars().all()
        return {
            "items": [
                {
                    "id": str(r.id),
                    "company_id": str(r.company_id) if r.company_id else None,
                    "trade_name": r.trade_name,
                    "official_domain": r.official_domain,
                    "website": r.website,
                    "status": r.status,
                    "confidence": r.confidence,
                }
                for r in rows
            ],
            "count": len(rows),
        }

    async def company_card(self, company_id: UUID) -> dict[str, Any] | None:
        row = (
            await self.session.execute(
                select(IgfCanonicalCompany).where(
                    IgfCanonicalCompany.deleted_at.is_(None),
                    or_(IgfCanonicalCompany.company_id == company_id, IgfCanonicalCompany.id == company_id),
                )
            )
        ).scalar_one_or_none()
        if not row:
            return None
        evidence = (
            await self.session.execute(
                select(IgfIdentityEvidence)
                .where(IgfIdentityEvidence.canonical_id == row.id, IgfIdentityEvidence.deleted_at.is_(None))
                .limit(40)
            )
        ).scalars().all()
        return {
            "canonical_id": str(row.id),
            "company_id": str(row.company_id) if row.company_id else None,
            "trade_name": row.trade_name,
            "legal_name": row.legal_name,
            "official_domain": row.official_domain,
            "website": row.website,
            "status": row.status,
            "confidence": row.confidence,
            "evidence": [
                {"source": e.source, "field": e.field, "value": e.value, "confidence": e.confidence, "verified": e.verified}
                for e in evidence
            ],
        }

    async def rebuild(self, *, limit: int = 1000, fetch_official: bool = False) -> dict[str, Any]:
        events = (
            await self.session.execute(
                select(RawEvent)
                .where(RawEvent.deleted_at.is_(None))
                .order_by(RawEvent.created_at.desc())
                .limit(limit)
            )
        ).scalars().all()
        existing = await self._existing_canonical()
        # Seed merge index from companies that already have verified domains
        # (use domain as merge key — company_id is linked later, not used as canonical PK)
        companies = (
            await self.session.execute(
                select(Company).where(Company.deleted_at.is_(None), Company.primary_domain.is_not(None))
            )
        ).scalars().all()
        for c in companies:
            existing.append(
                {
                    "id": f"seed:{c.primary_domain}",
                    "official_domain": c.primary_domain,
                    "trade_name": c.name,
                    "legal_name": c.name,
                    "aliases": [],
                }
            )

        payloads: list[dict[str, Any]] = []
        for event in events:
            meta = dict(getattr(event, "event_metadata", None) or getattr(event, "metadata", None) or {})
            payloads.append(
                {
                    "signal_id": str(event.id),
                    "raw_event_id": str(event.id),
                    "title": event.title or "",
                    "body": event.content or "",
                    "content": event.content or "",
                    "url": event.url,
                    "source": event.source,
                    "metadata": meta,
                    "official_website": meta.get("official_website") or meta.get("homepage") or meta.get("repo_homepage"),
                    "homepage": meta.get("homepage") or meta.get("repo_homepage"),
                    "github_homepage": meta.get("repo_homepage") or meta.get("homepage"),
                    "fetch_official_website": bool(fetch_official and event.source in {"product_hunt", "github_trending"}),
                    "fetch_product_hunt": bool(fetch_official and event.source == "product_hunt"),
                    "website_verified": bool(meta.get("official_website") or meta.get("repo_homepage")),
                    "industry": meta.get("industry"),
                }
            )

        snaps = self.pipeline.evaluate_many(payloads, existing=existing)
        metrics = self.rebuild_engine.build(snaps)

        created = 0
        for snap, event in zip(snaps, events, strict=False):
            dump = snap.model_dump(mode="json")
            company_id = None
            if snap.admission.allow_create_company and snap.domain and snap.canonical:
                company_id = await self._upsert_company(snap)
                if company_id:
                    created += 1
                    await self.session.flush()
            await self.persist_run(dump, raw_event_id=event.id, company_id=company_id, commit=False)

        # Ensure existing domain companies are ACTIVE canonicals
        for c in companies:
            await self._ensure_canonical_from_company(c)

        self.session.add(
            IgfFunnelSnapshot(
                id=uuid.uuid4(),
                payload=metrics.model_dump(mode="json"),
                signals=metrics.signals,
                candidates=metrics.candidates,
                official_websites=metrics.official_websites,
                verified_companies=metrics.verified_companies,
                scoring_version="igf-v1",
            )
        )
        await self.session.commit()
        return {
            **metrics.model_dump(mode="json"),
            "companies_created_or_linked": created,
            "seeded_from_existing_companies": len(companies),
        }

    async def _ensure_canonical_from_company(self, company: Company) -> None:
        if not company.primary_domain:
            return
        existing = (
            await self.session.execute(
                select(IgfCanonicalCompany).where(
                    IgfCanonicalCompany.deleted_at.is_(None),
                    IgfCanonicalCompany.official_domain == company.primary_domain,
                )
            )
        ).scalar_one_or_none()
        if existing:
            existing.company_id = existing.company_id or company.id
            existing.status = "ACTIVE"
            return
        attrs = company.attributes or {}
        self.session.add(
            IgfCanonicalCompany(
                id=uuid.uuid4(),
                company_id=company.id,
                legal_name=company.name,
                trade_name=company.name,
                normalized_key=_norm_key(company.name),
                aliases=[],
                official_domain=company.primary_domain,
                website=f"https://{company.primary_domain}",
                industry=company.industry,
                description=company.description,
                confidence=90.0,
                status="ACTIVE",
                verified_at=datetime.now(UTC),
                last_seen=datetime.now(UTC),
                collectors=[str(attrs.get("source") or "seed")],
                signals=[],
                payload={"seeded_from_company": True},
                evidence=[
                    {
                        "source": "identity_graph",
                        "field": "website",
                        "value": f"https://{company.primary_domain}",
                        "confidence": 90,
                        "verified": True,
                        "reason": "existing_verified_company_domain",
                    }
                ],
                scoring_version="igf-v1",
            )
        )

    async def _upsert_company(self, snap) -> UUID | None:
        domain = snap.domain
        name = snap.canonical.trade_name if snap.canonical else snap.candidate.name
        if not domain or not name:
            return None
        normalized = normalize_company_name(name)
        existing = (
            await self.session.execute(
                select(Company).where(
                    Company.deleted_at.is_(None),
                    or_(Company.primary_domain == domain, Company.normalized_name == normalized),
                )
            )
        ).scalar_one_or_none()
        attrs = {
            "igf_admitted": True,
            "igf_verified": True,
            "igf_identity_score": snap.score.score,
            "official_website": snap.website,
            "source": snap.source,
            "igf_evidence": [e.model_dump(mode="json") for e in snap.evidence_items[:12]],
        }
        if existing:
            existing.primary_domain = existing.primary_domain or domain
            existing.attributes = {**(existing.attributes or {}), **attrs}
            existing.last_seen_at = datetime.now(UTC)
            return existing.id
        company_id = uuid.uuid4()
        self.session.add(
            Company(
                id=company_id,
                name=name,
                normalized_name=normalized or domain,
                primary_domain=domain,
                description=snap.canonical.description if snap.canonical else None,
                industry=snap.canonical.industry if snap.canonical else None,
                last_seen_at=datetime.now(UTC),
                attributes=attrs,
            )
        )
        return company_id
