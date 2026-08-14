from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entity_resolution_erowd import (
    CanonicalEntityRow,
    EntityAliasRow,
    EntityCandidateRow,
    EntityResolutionRunRow,
    IdentityScoreRow,
    OfficialWebsiteRow,
    WebsiteAttributionRow,
    WebsiteValidationRow,
)
from app.models.intelligence import Company
from app.models.raw_event import RawEvent
from entity_resolution.pipelines.engine import ErowdPipeline
from entity_resolution.rebuild.engine import ErowdRebuildEngine
from intelligence.entity_resolution.normalization import normalize_company_name


class EntityResolutionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.pipeline = ErowdPipeline()
        self.rebuild_engine = ErowdRebuildEngine()

    def evaluate_signal(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.pipeline.evaluate(payload).model_dump(mode="json")

    async def persist_run(
        self,
        snap: dict[str, Any],
        *,
        raw_event_id: UUID | None = None,
        company_id: UUID | None = None,
        commit: bool = False,
    ) -> UUID:
        run_id = uuid.uuid4()
        self.session.add(
            EntityResolutionRunRow(
                id=run_id,
                signal_id=str(snap.get("signal_id") or ""),
                raw_event_id=raw_event_id,
                source=str(snap.get("source") or ""),
                verdict=str(snap.get("verdict") or "REJECTED"),
                admitted=bool((snap.get("admission") or {}).get("admitted")),
                identity_score=float((snap.get("score") or {}).get("score") or 0),
                payload=snap,
                evidence=list(snap.get("evidence") or []),
                scoring_version="erowd-v1",
            )
        )
        # Ensure the parent `entity_resolution_runs` row exists before inserting
        # children with `run_id` FK. Without an early flush, the async SQLAlchemy
        # flush ordering can attempt to insert `entity_candidates` first, causing
        # a foreign-key violation and rolling back the whole transaction.
        await self.session.flush()
        entity = snap.get("entity") or {}
        self.session.add(
            EntityCandidateRow(
                id=uuid.uuid4(),
                run_id=run_id,
                name=str(entity.get("name") or "unknown"),
                normalized_key=str(entity.get("normalized_key") or "unknown"),
                aliases=list(entity.get("aliases") or []),
                organization=entity.get("organization"),
                domain=entity.get("domain"),
                official_website=entity.get("official_website"),
                payload=entity,
            )
        )
        website = snap.get("website") or {}
        if website.get("discovered") and website.get("domain"):
            self.session.add(
                OfficialWebsiteRow(
                    id=uuid.uuid4(),
                    domain=str(website["domain"]),
                    website=str(website.get("website") or ""),
                    discovered=True,
                    source=str(website.get("source") or ""),
                    confidence=float(website.get("confidence") or 0),
                    verified_at=datetime.now(UTC),
                    signal_id=str(snap.get("signal_id") or ""),
                    payload=website,
                    evidence=list(website.get("evidence") or []),
                )
            )
            attr = snap.get("attribution") or {}
            self.session.add(
                WebsiteAttributionRow(
                    id=uuid.uuid4(),
                    website=attr.get("website"),
                    domain=attr.get("domain"),
                    discovery_source=str(attr.get("discovery_source") or ""),
                    collector=str(attr.get("collector") or ""),
                    confidence=float(attr.get("confidence") or 0),
                    attributed_at=datetime.now(UTC),
                    signal_id=str(snap.get("signal_id") or ""),
                    payload=attr,
                    evidence=list(attr.get("evidence") or []),
                )
            )
        score = snap.get("score") or {}
        self.session.add(
            IdentityScoreRow(
                id=uuid.uuid4(),
                signal_id=str(snap.get("signal_id") or ""),
                domain=(snap.get("website") or {}).get("domain"),
                score=float(score.get("score") or 0),
                passed=bool(score.get("passed")),
                breakdown=score,
                evidence=list(score.get("evidence") or []),
                scoring_version="erowd-v1",
            )
        )
        validation = snap.get("validation") or {}
        if validation.get("domain"):
            self.session.add(
                WebsiteValidationRow(
                    id=uuid.uuid4(),
                    domain=str(validation["domain"]),
                    website=(snap.get("website") or {}).get("website"),
                    verified=bool(validation.get("verified")),
                    https=bool(validation.get("https")),
                    reason=str(validation.get("reason") or ""),
                    title=validation.get("title"),
                    favicon_url=validation.get("favicon_url"),
                    payload=validation,
                    evidence=list(validation.get("evidence") or []),
                )
            )
        identity = snap.get("identity") or {}
        if (snap.get("admission") or {}).get("admitted") and identity.get("domain"):
            canon_id = uuid.uuid4()
            self.session.add(
                CanonicalEntityRow(
                    id=canon_id,
                    company_name=str(identity.get("company_name") or ""),
                    normalized_key=normalize_company_name(str(identity.get("company_name") or "")),
                    official_website=identity.get("official_website"),
                    domain=identity.get("domain"),
                    logo_url=identity.get("logo_url"),
                    industry=identity.get("industry"),
                    country=identity.get("country"),
                    linkedin_url=identity.get("linkedin_url"),
                    description=identity.get("description"),
                    confidence=float(identity.get("confidence") or 0),
                    company_id=company_id,
                    payload=identity,
                    evidence=list(identity.get("evidence") or []),
                )
            )
            for alias in (entity.get("aliases") or [])[:8]:
                self.session.add(
                    EntityAliasRow(
                        id=uuid.uuid4(),
                        canonical_entity_id=canon_id,
                        alias=str(alias),
                        normalized_alias=normalize_company_name(str(alias)),
                        domain=identity.get("domain"),
                        payload={"alias": alias},
                    )
                )
        await self.session.flush()
        if commit:
            await self.session.commit()
        return run_id

    async def company_card(self, company_id: UUID) -> dict[str, Any] | None:
        company = await self.session.get(Company, company_id)
        if not company:
            return None
        canon = await self.session.scalar(
            select(CanonicalEntityRow)
            .where(
                CanonicalEntityRow.deleted_at.is_(None),
                or_(
                    CanonicalEntityRow.company_id == company_id,
                    CanonicalEntityRow.domain == company.primary_domain,
                ),
            )
            .order_by(CanonicalEntityRow.created_at.desc())
            .limit(1)
        )
        attrs = company.attributes or {}
        return {
            "company_id": str(company_id),
            "company_name": company.name,
            "official_website": (canon.official_website if canon else None) or (f"https://{company.primary_domain}" if company.primary_domain else None),
            "domain": (canon.domain if canon else None) or company.primary_domain,
            "verified": bool(attrs.get("erowd_verified") or (canon and canon.confidence >= 90)),
            "confidence": float(canon.confidence if canon else attrs.get("erowd_identity_score") or 0),
            "evidence": (canon.evidence if canon else attrs.get("erowd_evidence") or []),
            "collector": attrs.get("source"),
            "discovery_source": attrs.get("erowd_discovery_source") or attrs.get("cre_attribution"),
        }

    async def search(self, q: str, *, limit: int = 40) -> dict[str, Any]:
        pattern = f"%{q.lower()}%"
        rows = list(
            (
                await self.session.scalars(
                    select(CanonicalEntityRow)
                    .where(
                        CanonicalEntityRow.deleted_at.is_(None),
                        or_(
                            func.lower(CanonicalEntityRow.company_name).like(pattern),
                            func.lower(CanonicalEntityRow.domain).like(pattern),
                        ),
                    )
                    .order_by(CanonicalEntityRow.confidence.desc())
                    .limit(limit)
                )
            ).all()
        )
        return {
            "items": [
                {
                    "company": r.company_name,
                    "website": r.official_website,
                    "domain": r.domain,
                    "confidence": r.confidence,
                    "verified": r.confidence >= 90,
                }
                for r in rows
            ]
        }

    async def dashboard(self) -> dict[str, Any]:
        runs = list(
            (
                await self.session.scalars(
                    select(EntityResolutionRunRow)
                    .where(EntityResolutionRunRow.deleted_at.is_(None))
                    .order_by(EntityResolutionRunRow.created_at.desc())
                    .limit(100)
                )
            ).all()
        )
        items = []
        for r in runs:
            p = r.payload or {}
            identity = p.get("identity") or {}
            website = p.get("website") or {}
            validation = p.get("validation") or {}
            attr = p.get("attribution") or {}
            items.append(
                {
                    "company": identity.get("company_name") or (p.get("entity") or {}).get("name"),
                    "official_website": identity.get("official_website") or website.get("website"),
                    "confidence": r.identity_score,
                    "verified": bool(validation.get("verified")),
                    "source": attr.get("discovery_source") or website.get("source"),
                    "collector": r.source,
                    "evidence_count": len(p.get("evidence_edges") or p.get("evidence") or []),
                    "status": r.verdict,
                    "admitted": r.admitted,
                    "rejected": not r.admitted,
                }
            )
        return {
            "items": items,
            "admitted": sum(1 for r in runs if r.admitted),
            "rejected": sum(1 for r in runs if not r.admitted),
            "scoring_version": "erowd-v1",
        }

    async def report(self) -> dict[str, Any]:
        runs = list(
            (await self.session.scalars(select(EntityResolutionRunRow).where(EntityResolutionRunRow.deleted_at.is_(None)).limit(2000))).all()
        )
        from entity_resolution.models.types import ErowdSnapshot

        snaps = []
        for r in runs:
            if r.payload:
                try:
                    snaps.append(ErowdSnapshot.model_validate(r.payload))
                except Exception:  # noqa: BLE001
                    continue
        if not snaps:
            return {"status": "empty", "total_signals": 0}
        return self.rebuild_engine.build(snaps).model_dump(mode="json")

    async def rebuild(self, *, limit: int = 1000, fetch_official: bool = False) -> dict[str, Any]:
        events = list((await self.session.scalars(select(RawEvent).order_by(RawEvent.created_at.desc()).limit(limit))).all())
        snaps = []
        created = 0
        for event in events:
            meta = dict(event.event_metadata or {})
            payload = {
                "signal_id": str(event.id),
                "title": event.title or "",
                "body": event.content or "",
                "content": event.content or "",
                "url": event.url,
                "source": event.source,
                "metadata": meta,
                "fetch_official_website": fetch_official and event.source in {"product_hunt", "github_trending"},
                "fetch_product_hunt": fetch_official and event.source == "product_hunt",
                "official_website": meta.get("official_website") or meta.get("product_website") or meta.get("homepage"),
                "homepage": meta.get("homepage"),
                "github_homepage": meta.get("repo_homepage") or meta.get("github_homepage") or meta.get("homepage"),
                "org_website": meta.get("org_website"),
                "website_verified": bool(
                    meta.get("official_website") or meta.get("product_website") or meta.get("repo_homepage")
                ),
                "industry": meta.get("industry") or ("Software" if event.source == "product_hunt" else None),
            }
            snap = self.pipeline.evaluate(payload)
            snaps.append(snap)
            data = snap.model_dump(mode="json")
            company_id = None
            if snap.admission.allow_create_company and snap.identity.domain and snap.identity.company_name:
                existing = await self.session.scalar(
                    select(Company).where(Company.normalized_name == normalize_company_name(snap.identity.company_name))
                )
                attrs = {
                    "erowd_verified": True,
                    "erowd_identity_score": snap.score.score,
                    "erowd_discovery_source": snap.website.source,
                    "erowd_evidence": snap.website.evidence,
                    "source": event.source,
                    "source_url": event.url,
                    "official_website": snap.identity.official_website,
                }
                if existing is None:
                    company = Company(
                        id=uuid.uuid4(),
                        name=snap.identity.company_name,
                        normalized_name=normalize_company_name(snap.identity.company_name),
                        primary_domain=snap.identity.domain,
                        description=snap.identity.description,
                        industry=snap.identity.industry,
                        last_seen_at=event.published_at or event.created_at,
                        attributes=attrs,
                    )
                    self.session.add(company)
                    company_id = company.id
                    created += 1
                else:
                    if existing.deleted_at is not None:
                        existing.deleted_at = None
                        created += 1
                    existing.primary_domain = snap.identity.domain or existing.primary_domain
                    existing.attributes = {**(existing.attributes or {}), **attrs}
                    company_id = existing.id
            await self.persist_run(data, raw_event_id=event.id, company_id=company_id, commit=False)
        await self.session.commit()
        report = self.rebuild_engine.build(snaps)
        out = report.model_dump(mode="json")
        out["companies_created"] = created
        return out
