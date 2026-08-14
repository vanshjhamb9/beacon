from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.models.identity_coverage import (
    IdentityAliasGraph,
    IdentityCollectorMetric,
    IdentityCoverageSnapshot,
    IdentityDailyReport,
    IdentityDomainIntelligence,
    IdentityProviderResult,
    IdentityRecoveryQueue,
)
from app.models.intelligence import Company
from app.models.raw_event import RawEvent
from app.services.identity_graph import IdentityGraphService
from identity_coverage.pipelines.engine import IdentityCoveragePipeline
from identity_coverage.rebuild.engine import IceRebuildEngine
from identity_graph.pipelines.engine import IdentityResolutionPipeline


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (name or "").lower()) or "unknown"


class IdentityCoverageService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.pipeline = IdentityCoveragePipeline()
        self.igf = IdentityResolutionPipeline()
        self.igf_service = IdentityGraphService(session)
        self.rebuild_engine = IceRebuildEngine()

    def evaluate(self, payload: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        return self.pipeline.evaluate(payload, **kwargs).model_dump(mode="json")

    async def dashboard(self) -> dict[str, Any]:
        latest = (
            await self.session.execute(
                select(IdentityDailyReport)
                .where(IdentityDailyReport.deleted_at.is_(None))
                .order_by(IdentityDailyReport.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        companies = (
            await self.session.execute(
                select(func.count()).select_from(Company).where(
                    Company.deleted_at.is_(None), Company.primary_domain.is_not(None)
                )
            )
        ).scalar() or 0
        rows = (
            await self.session.execute(select(Company).where(Company.deleted_at.is_(None)))
        ).scalars().all()
        emails = sum(
            1
            for c in rows
            if (c.attributes or {}).get("business_email") or (c.attributes or {}).get("ofc_business_email")
        )
        dms = sum(1 for c in rows if (c.attributes or {}).get("decision_maker"))

        pending = (
            await self.session.execute(
                select(func.count()).select_from(IdentityRecoveryQueue).where(
                    IdentityRecoveryQueue.deleted_at.is_(None),
                    IdentityRecoveryQueue.status == "pending",
                )
            )
        ).scalar() or 0
        collectors = (
            await self.session.execute(
                select(IdentityCollectorMetric)
                .where(IdentityCollectorMetric.deleted_at.is_(None))
                .order_by(IdentityCollectorMetric.created_at.desc())
                .limit(20)
            )
        ).scalars().all()
        payload = dict(latest.payload) if latest else {}
        return {
            "scoring_version": "ice-v1",
            "verified_companies": int(companies),
            "business_emails": int(emails),
            "decision_makers": int(dms),
            "sales_ready": int(payload.get("after", {}).get("sales_ready") or 0),
            "revenue_ready": int(latest.revenue_ready if latest else 0),
            "recovery_pending": int(pending),
            "coverage_pct": float(latest.coverage_pct if latest else 0),
            "vansh_ready_answer": latest.vansh_ready_answer if latest else "NO",
            "funnel": (payload.get("funnel") or {}),
            "collectors": [
                {
                    "collector": c.collector,
                    "recommendation": c.recommendation,
                    "signals": c.signals,
                    "companies": c.companies,
                    "official_websites": c.official_websites,
                    "business_emails": c.business_emails,
                    "revenue_ready": c.revenue_ready,
                    "identity_precision": c.identity_precision,
                    "identity_recall": c.identity_recall,
                }
                for c in collectors
            ],
            "business_impact": payload.get("business_impact") or {},
            "top_rejections": payload.get("top_rejections") or {},
        }

    async def company_card(self, company_id: UUID) -> dict[str, Any] | None:
        company = await self.session.get(Company, company_id)
        if not company or company.deleted_at:
            return None
        attrs = company.attributes or {}
        domain = company.primary_domain
        evidence_rows = (
            await self.session.execute(
                select(IdentityProviderResult)
                .join(
                    IdentityCoverageSnapshot,
                    IdentityProviderResult.snapshot_id == IdentityCoverageSnapshot.id,
                    isouter=True,
                )
                .where(IdentityCoverageSnapshot.domain == domain)
                .limit(40)
            )
        ).scalars().all() if domain else []
        return {
            "company_id": str(company.id),
            "name": company.name,
            "domain": domain,
            "website": f"https://{domain}" if domain else None,
            "business_email": attrs.get("business_email") or attrs.get("ofc_business_email"),
            "decision_maker": attrs.get("decision_maker"),
            "evidence": [
                {
                    "provider": e.provider,
                    "field": e.field,
                    "value": e.value,
                    "confidence": e.confidence,
                    "verified": e.verified,
                    "collector": e.collector,
                }
                for e in evidence_rows
            ],
            "attributes": {
                k: v
                for k, v in attrs.items()
                if k in {"source", "igf_admitted", "ice_recovered_at", "ofc_linkedin", "why_now"}
            },
        }

    async def recovery_queue(self, *, limit: int = 50) -> dict[str, Any]:
        rows = (
            await self.session.execute(
                select(IdentityRecoveryQueue)
                .where(IdentityRecoveryQueue.deleted_at.is_(None), IdentityRecoveryQueue.status == "pending")
                .order_by(IdentityRecoveryQueue.created_at.desc())
                .limit(limit)
            )
        ).scalars().all()
        return {
            "items": [
                {
                    "id": str(r.id),
                    "signal_id": r.signal_id,
                    "reason": r.reason,
                    "domain": r.domain,
                    "attempts": r.attempts,
                    "status": r.status,
                }
                for r in rows
            ],
            "count": len(rows),
        }

    async def providers(self) -> dict[str, Any]:
        return {
            "providers": [
                {"name": "product_hunt_api", "priority": 10, "requires": ["PRODUCT_HUNT_DEVELOPER_TOKEN"]},
                {"name": "github_identity", "priority": 15, "requires": ["GITHUB_TOKEN (optional)"]},
                {"name": "website_intelligence", "priority": 20, "requires": []},
                {"name": "domain_intelligence", "priority": 35, "requires": []},
            ]
        }

    async def collectors(self) -> dict[str, Any]:
        dash = await self.dashboard()
        return {"collectors": dash.get("collectors") or []}

    async def reports(self) -> dict[str, Any]:
        rows = (
            await self.session.execute(
                select(IdentityDailyReport)
                .where(IdentityDailyReport.deleted_at.is_(None))
                .order_by(IdentityDailyReport.created_at.desc())
                .limit(14)
            )
        ).scalars().all()
        return {
            "items": [
                {
                    "id": str(r.id),
                    "coverage_pct": r.coverage_pct,
                    "revenue_ready": r.revenue_ready,
                    "vansh_ready_answer": r.vansh_ready_answer,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "payload": r.payload,
                }
                for r in rows
            ]
        }

    async def retry_missing(self, *, limit: int = 40) -> dict[str, Any]:
        return await self.expand(limit=limit, fetch_github=True, crawl_website=True, probe_dns=False)

    async def expand(
        self,
        *,
        limit: int = 800,
        fetch_github: bool = True,
        crawl_website: bool = True,
        probe_dns: bool = False,
        github_fetch_cap: int = 60,
    ) -> dict[str, Any]:
        before = await self._live_kpis()
        events = (
            await self.session.execute(
                select(RawEvent)
                .where(RawEvent.deleted_at.is_(None))
                .order_by(RawEvent.created_at.desc())
                .limit(limit)
            )
        ).scalars().all()

        existing = await self.igf_service._existing_canonical()
        snaps = []
        collector_rows: list[dict[str, Any]] = []
        gh_fetches = 0
        created = 0

        for event in events:
            meta = dict(getattr(event, "event_metadata", None) or {})
            payload = {
                "signal_id": str(event.id),
                "title": event.title or "",
                "body": event.content or "",
                "content": event.content or "",
                "url": event.url,
                "source": event.source,
                "metadata": meta,
                "official_website": meta.get("official_website") or meta.get("homepage") or meta.get("repo_homepage"),
                "homepage": meta.get("homepage") or meta.get("repo_homepage"),
                "github_homepage": meta.get("repo_homepage"),
            }
            do_gh = (
                fetch_github
                and event.source == "github_trending"
                and not payload.get("official_website")
                and gh_fetches < github_fetch_cap
            )
            if do_gh:
                gh_fetches += 1
            ice = self.pipeline.evaluate(
                payload,
                fetch_github=do_gh,
                crawl_website=False,  # crawl after admit on domain companies
                probe_dns=False,
            )
            snaps.append(ice)
            enriched = self.pipeline.to_igf_payload(payload, ice)
            igf_snap = self.igf.evaluate(enriched, existing=existing)

            snapshot_id = uuid.uuid4()
            self.session.add(
                IdentityCoverageSnapshot(
                    id=snapshot_id,
                    signal_id=str(event.id),
                    source=event.source,
                    domain=ice.domain,
                    website=ice.website,
                    admitted_hint=ice.admitted_hint,
                    payload=ice.model_dump(mode="json"),
                    evidence=[e.model_dump(mode="json") for e in ice.evidence],
                    scoring_version="ice-v1",
                )
            )
            await self.session.flush()
            for ev in ice.evidence[:20]:
                self.session.add(
                    IdentityProviderResult(
                        id=uuid.uuid4(),
                        snapshot_id=snapshot_id,
                        provider=ev.source,
                        field=ev.field,
                        value=ev.value,
                        confidence=ev.confidence,
                        collector=ev.collector,
                        verified=ev.verification,
                        priority=ev.priority,
                        payload=ev.model_dump(mode="json"),
                    )
                )
            for reason in ice.recovery:
                self.session.add(
                    IdentityRecoveryQueue(
                        id=uuid.uuid4(),
                        signal_id=str(event.id),
                        reason=reason.value,
                        domain=ice.domain,
                        attempts=0,
                        status="pending",
                        payload={"source": event.source},
                    )
                )

            company_id = None
            if igf_snap.admission.allow_create_company and igf_snap.domain and igf_snap.canonical:
                company_id = await self.igf_service._upsert_company(igf_snap)
                if company_id:
                    created += 1
                    await self.session.flush()
                    existing.append(
                        {
                            "id": str(company_id),
                            "official_domain": igf_snap.domain,
                            "trade_name": igf_snap.canonical.trade_name,
                            "legal_name": igf_snap.canonical.legal_name,
                            "aliases": igf_snap.canonical.aliases,
                        }
                    )
                if ice.alias:
                    self.session.add(
                        IdentityAliasGraph(
                            id=uuid.uuid4(),
                            primary_name=ice.alias.primary_name,
                            normalized_key=_norm(ice.alias.primary_name),
                            aliases=list(ice.alias.aliases),
                            official_domain=ice.domain,
                            confidence=ice.alias.confidence,
                            reason=ice.alias.reason,
                            merge_evidence=list(ice.alias.merge_evidence),
                            company_id=company_id,
                            payload=ice.alias.model_dump(mode="json"),
                        )
                    )
            await self.igf_service.persist_run(
                igf_snap.model_dump(mode="json"),
                raw_event_id=event.id,
                company_id=company_id,
                commit=False,
            )
            collector_rows.append(
                {
                    "collector": event.source,
                    "candidate": True,
                    "admitted": igf_snap.admission.admitted,
                    "company": bool(company_id),
                    "website": ice.website,
                    "official_website": ice.website,
                    "business_email": (ice.ranked.get("business_email").value if ice.ranked.get("business_email") else None),
                    "decision_maker": (ice.ranked.get("decision_maker").value if ice.ranked.get("decision_maker") else None),
                    "confidence": igf_snap.score.score,
                    "duplicate": 1 if igf_snap.merge.merged else 0,
                }
            )

        # Website intel + contacts on all domain companies
        companies = (
            await self.session.execute(
                select(Company).where(Company.deleted_at.is_(None), Company.primary_domain.is_not(None))
            )
        ).scalars().all()
        if crawl_website:
            for company in companies:
                site_payload = {
                    "signal_id": str(company.id),
                    "source": (company.attributes or {}).get("source") or "website",
                    "official_website": f"https://{company.primary_domain}",
                    "official_domain": company.primary_domain,
                    "metadata": {},
                }
                site_ev = self.pipeline.website.collect(site_payload)
                if probe_dns:
                    dns_ev = self.pipeline.domain.collect(site_payload, probe=True)
                    dns_ok = any(e.field == "dns_ok" and e.value == "true" for e in dns_ev)
                    ssl_ok = any(e.field == "ssl_ok" and e.value == "true" for e in dns_ev)
                    mx = next((e.value for e in dns_ev if e.field == "mx"), None)
                    self.session.add(
                        IdentityDomainIntelligence(
                            id=uuid.uuid4(),
                            domain=company.primary_domain,
                            dns_ok=dns_ok,
                            ssl_ok=ssl_ok,
                            mx=mx,
                            payload={"probed": True},
                            evidence=[e.model_dump(mode="json") for e in dns_ev],
                        )
                    )
                attrs = dict(company.attributes or {})
                for ev in site_ev:
                    if ev.field == "business_email" and not attrs.get("business_email"):
                        attrs["business_email"] = ev.value
                        attrs["ofc_business_email"] = ev.value
                    if ev.field == "decision_maker" and not attrs.get("decision_maker"):
                        attrs["decision_maker"] = ev.value
                    if ev.field == "linkedin_company" and not attrs.get("linkedin_company"):
                        attrs["linkedin_company"] = ev.value
                attrs["ice_recovered_at"] = datetime.now(UTC).isoformat()
                company.attributes = attrs
                flag_modified(company, "attributes")

        after = await self._live_kpis()
        after["signals"] = len(events)
        after["companies_created"] = created
        after["github_live_fetches"] = gh_fetches

        audit = self.rebuild_engine.audit(
            before=before,
            after=after,
            snaps=snaps,
            collector_rows=collector_rows,
        )
        for c in audit.collectors:
            self.session.add(
                IdentityCollectorMetric(
                    id=uuid.uuid4(),
                    collector=c.collector,
                    recommendation=c.recommendation.value,
                    signals=c.signals,
                    companies=c.companies,
                    official_websites=c.official_websites,
                    business_emails=c.business_emails,
                    decision_makers=c.decision_makers,
                    revenue_ready=c.revenue_ready,
                    identity_precision=c.identity_precision,
                    identity_recall=c.identity_recall,
                    payload=c.model_dump(mode="json"),
                )
            )
        self.session.add(
            IdentityDailyReport(
                id=uuid.uuid4(),
                payload=audit.model_dump(mode="json"),
                coverage_pct=audit.coverage_pct,
                revenue_ready=audit.business_impact.revenue_ready,
                vansh_ready_answer=audit.vansh_ready_answer,
                scoring_version="ice-v1",
            )
        )
        await self.session.commit()
        return {
            "before": before,
            "after": after,
            "audit": audit.model_dump(mode="json"),
            "created": created,
            "github_live_fetches": gh_fetches,
        }

    async def _live_kpis(self) -> dict[str, Any]:
        companies = (
            await self.session.execute(select(Company).where(Company.deleted_at.is_(None)))
        ).scalars().all()
        with_domain = [c for c in companies if c.primary_domain]
        emails = sum(
            1
            for c in with_domain
            if (c.attributes or {}).get("business_email") or (c.attributes or {}).get("ofc_business_email")
        )
        dms = sum(1 for c in with_domain if (c.attributes or {}).get("decision_maker"))
        return {
            "companies": len(companies),
            "verified_companies": len(with_domain),
            "official_websites": len(with_domain),
            "business_emails": emails,
            "decision_makers": dms,
            "sales_ready": 0,
            "revenue_ready": 0,
        }
