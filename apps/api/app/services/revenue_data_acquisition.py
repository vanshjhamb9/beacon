from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.models.intelligence import Company
from app.models.raw_event import RawEvent
from app.models.revenue_data_acquisition import (
    RdapCompanyProfile,
    RdapConnectorScore,
    RdapContactRecovery,
    RdapDailyReport,
    RdapDmRecovery,
    RdapRecoveryQueue,
    RdapRevenueYield,
    RdapSourceMetric,
)
from app.services.identity_graph import IdentityGraphService
from identity_graph.pipelines.engine import IdentityResolutionPipeline
from revenue_data_acquisition.pipelines.engine import RevenueDataAcquisitionPipeline
from revenue_data_acquisition.rebuild.engine import RdapRebuildEngine
from revenue_data_acquisition.source_roles.engine import SourceClassificationEngine


class RevenueDataAcquisitionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.pipeline = RevenueDataAcquisitionPipeline()
        self.rebuild = RdapRebuildEngine()
        self.roles = SourceClassificationEngine()
        self.igf = IdentityResolutionPipeline()
        self.igf_service = IdentityGraphService(session)

    def evaluate(self, payload: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        return self.pipeline.evaluate(payload, **kwargs).model_dump(mode="json")

    async def dashboard(self) -> dict[str, Any]:
        latest = (
            await self.session.execute(
                select(RdapDailyReport)
                .where(RdapDailyReport.deleted_at.is_(None))
                .order_by(RdapDailyReport.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        kpis = await self._live_kpis()
        pending = (
            await self.session.execute(
                select(func.count())
                .select_from(RdapRecoveryQueue)
                .where(RdapRecoveryQueue.deleted_at.is_(None), RdapRecoveryQueue.status == "pending")
            )
        ).scalar() or 0
        connectors = (
            await self.session.execute(
                select(RdapConnectorScore)
                .where(RdapConnectorScore.deleted_at.is_(None))
                .order_by(RdapConnectorScore.created_at.desc())
                .limit(30)
            )
        ).scalars().all()
        payload = dict(latest.payload) if latest else {}
        return {
            "scoring_version": "rdap-v1",
            "verified_companies": kpis["verified_companies"],
            "official_websites": kpis["official_websites"],
            "business_emails": kpis["business_emails"],
            "decision_makers": kpis["decision_makers"],
            "sales_ready": kpis["sales_ready"],
            "revenue_ready": kpis["revenue_ready"],
            "recovery_pending": int(pending),
            "vansh_ready_answer": latest.vansh_ready_answer if latest else "NO",
            "funnel": payload.get("funnel") or [],
            "connectors": [
                {
                    "connector": c.connector,
                    "grade": c.grade,
                    "verified_companies": c.verified_companies,
                    "business_emails": c.business_emails,
                    "decision_makers": c.decision_makers,
                    "revenue_ready": c.revenue_ready,
                    "revenue_yield": c.revenue_yield,
                    **(c.payload or {}),
                }
                for c in connectors
            ],
            "yields": payload.get("yields") or [],
            "top_rejections": payload.get("top_rejections") or {},
            "top_revenue_ready": payload.get("top_revenue_ready") or [],
            "daily": {
                "new_companies": int((payload.get("after") or {}).get("verified_companies") or 0)
                - int((payload.get("before") or {}).get("verified_companies") or 0),
                "new_emails": int((payload.get("after") or {}).get("business_emails") or 0)
                - int((payload.get("before") or {}).get("business_emails") or 0),
                "new_decision_makers": int((payload.get("after") or {}).get("decision_makers") or 0)
                - int((payload.get("before") or {}).get("decision_makers") or 0),
                "new_sales_ready": int((payload.get("after") or {}).get("sales_ready") or 0)
                - int((payload.get("before") or {}).get("sales_ready") or 0),
                "new_revenue_ready": int((payload.get("after") or {}).get("revenue_ready") or 0)
                - int((payload.get("before") or {}).get("revenue_ready") or 0),
            },
            "before": payload.get("before") or {},
            "after": payload.get("after") or kpis,
        }

    async def company_dossier(self, company_id: UUID) -> dict[str, Any] | None:
        company = await self.session.get(Company, company_id)
        if not company or company.deleted_at:
            return None
        profile = (
            await self.session.execute(
                select(RdapCompanyProfile)
                .where(RdapCompanyProfile.deleted_at.is_(None), RdapCompanyProfile.company_id == company_id)
                .order_by(RdapCompanyProfile.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        attrs = company.attributes or {}
        dossier = dict(profile.dossier) if profile else {}
        if not dossier:
            dossier = {
                "identity": {"trade_name": company.name, "legal_name": company.name},
                "website": {"value": f"https://{company.primary_domain}"} if company.primary_domain else None,
                "contacts": (
                    [{"value": attrs.get("business_email") or attrs.get("ofc_business_email")}]
                    if attrs.get("business_email") or attrs.get("ofc_business_email")
                    else []
                ),
                "decision_makers": (
                    [{"name": attrs.get("decision_maker"), "role": "unknown"}]
                    if attrs.get("decision_maker")
                    else []
                ),
                "trust_score": profile.trust_score if profile else 0,
                "sales_ready": bool(profile.sales_ready) if profile else False,
                "revenue_ready": bool(profile.revenue_ready) if profile else False,
            }
        return {
            "company_id": str(company.id),
            "name": company.name,
            "domain": company.primary_domain,
            "dossier": dossier,
            "sales_ready": bool(profile.sales_ready) if profile else False,
            "revenue_ready": bool(profile.revenue_ready) if profile else False,
            "attributes": {
                k: v
                for k, v in attrs.items()
                if k
                in {
                    "source",
                    "business_email",
                    "ofc_business_email",
                    "decision_maker",
                    "rdap_recovered_at",
                    "why_now",
                }
            },
        }

    async def recovery_queue(self, *, limit: int = 50) -> dict[str, Any]:
        rows = (
            await self.session.execute(
                select(RdapRecoveryQueue)
                .where(RdapRecoveryQueue.deleted_at.is_(None), RdapRecoveryQueue.status == "pending")
                .order_by(RdapRecoveryQueue.created_at.desc())
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

    async def connectors(self) -> dict[str, Any]:
        dash = await self.dashboard()
        return {"connectors": dash.get("connectors") or []}

    async def revenue_yield(self) -> dict[str, Any]:
        rows = (
            await self.session.execute(
                select(RdapRevenueYield)
                .where(RdapRevenueYield.deleted_at.is_(None))
                .order_by(RdapRevenueYield.created_at.desc())
                .limit(40)
            )
        ).scalars().all()
        if rows:
            return {
                "items": [
                    {
                        "connector": r.connector,
                        "signals": r.signals,
                        "companies": r.companies,
                        "emails": r.emails,
                        "decision_makers": r.decision_makers,
                        "revenue_ready": r.revenue_ready,
                        "yield_pct": r.yield_pct,
                    }
                    for r in rows
                ]
            }
        dash = await self.dashboard()
        return {"items": dash.get("yields") or []}

    async def reports(self) -> dict[str, Any]:
        rows = (
            await self.session.execute(
                select(RdapDailyReport)
                .where(RdapDailyReport.deleted_at.is_(None))
                .order_by(RdapDailyReport.created_at.desc())
                .limit(14)
            )
        ).scalars().all()
        return {
            "items": [
                {
                    "id": str(r.id),
                    "verified_companies": r.verified_companies,
                    "business_emails": r.business_emails,
                    "decision_makers": r.decision_makers,
                    "sales_ready": r.sales_ready,
                    "revenue_ready": r.revenue_ready,
                    "vansh_ready_answer": r.vansh_ready_answer,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "payload": r.payload,
                }
                for r in rows
            ]
        }

    async def recover_contacts(self, *, limit: int = 80) -> dict[str, Any]:
        return await self.expand(
            limit=limit,
            fetch_github=False,
            recover_contacts=True,
            recover_dms=False,
            crawl_companies=True,
        )

    async def recover_decision_makers(self, *, limit: int = 80) -> dict[str, Any]:
        return await self.expand(
            limit=limit,
            fetch_github=False,
            recover_contacts=False,
            recover_dms=True,
            crawl_companies=True,
        )

    async def retry_recovery(self, *, limit: int = 40) -> dict[str, Any]:
        cutoff = datetime.now(UTC) - timedelta(hours=24)
        rows = (
            await self.session.execute(
                select(RdapRecoveryQueue)
                .where(
                    RdapRecoveryQueue.deleted_at.is_(None),
                    RdapRecoveryQueue.status == "pending",
                    RdapRecoveryQueue.created_at <= cutoff,
                )
                .limit(limit)
            )
        ).scalars().all()
        for row in rows:
            row.attempts = int(row.attempts or 0) + 1
            row.status = "retrying"
        await self.session.flush()
        result = await self.expand(
            limit=max(limit, 100),
            fetch_github=True,
            recover_contacts=True,
            recover_dms=True,
            crawl_companies=True,
            github_fetch_cap=40,
        )
        for row in rows:
            row.status = "pending"
        await self.session.commit()
        return {"retried": len(rows), **result}

    async def expand(
        self,
        *,
        limit: int = 800,
        fetch_github: bool = True,
        recover_contacts: bool = True,
        recover_dms: bool = True,
        crawl_companies: bool = True,
        github_fetch_cap: int = 60,
        company_crawl_cap: int = 120,
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
                "confidence": meta.get("confidence") or 0,
            }
            do_gh = (
                fetch_github
                and event.source == "github_trending"
                and not payload.get("official_website")
                and gh_fetches < github_fetch_cap
            )
            if do_gh:
                gh_fetches += 1

            # Signal-level: discover website only (no crawl storms on every signal)
            rdap = self.pipeline.evaluate(
                payload,
                fetch_github=do_gh,
                recover_contacts=False,
                recover_dms=False,
            )
            snaps.append(rdap)

            enriched = {
                **payload,
                **(rdap.payload.get("igf_enrichment") or {}),
            }
            company_id = None
            if rdap.can_create_identity and rdap.domain:
                igf_snap = self.igf.evaluate(enriched, existing=existing)
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
                await self.igf_service.persist_run(
                    igf_snap.model_dump(mode="json"),
                    raw_event_id=event.id,
                    company_id=company_id,
                    commit=False,
                )

            for reason in rdap.recovery:
                self.session.add(
                    RdapRecoveryQueue(
                        id=uuid.uuid4(),
                        signal_id=str(event.id),
                        company_id=company_id,
                        reason=reason.value,
                        domain=rdap.domain,
                        attempts=0,
                        status="pending",
                        payload={"source": event.source, "roles": [r.value for r in rdap.roles]},
                    )
                )

            collector_rows.append(
                {
                    "connector": event.source,
                    "source": event.source,
                    "candidate": rdap.can_create_identity,
                    "company": bool(company_id),
                    "verified_company": bool(company_id),
                    "website": rdap.website,
                    "business_email": None,
                    "decision_maker": None,
                    "confidence": rdap.confidence,
                    "duplicate": 0,
                    "sales_ready": False,
                    "revenue_ready": False,
                }
            )

        # Company-level contact + DM recovery on verified domains
        companies = (
            await self.session.execute(
                select(Company).where(Company.deleted_at.is_(None), Company.primary_domain.is_not(None))
            )
        ).scalars().all()
        top_rr: list[dict[str, Any]] = []
        crawled = 0
        if crawl_companies:
            for company in companies:
                if crawled >= company_crawl_cap:
                    break
                attrs = dict(company.attributes or {})
                website = f"https://{company.primary_domain}"
                source = str(attrs.get("source") or "official_website")
                need_email = recover_contacts and not (attrs.get("business_email") or attrs.get("ofc_business_email"))
                need_dm = recover_dms and not attrs.get("decision_maker")
                crawled += 1
                site_payload = {
                    "signal_id": str(company.id),
                    "title": company.name,
                    "source": source,
                    "official_website": website,
                    "website": website,
                    "metadata": {
                        "company_hints": [company.name],
                        "buying_signals": attrs.get("buying_signals") or [],
                        "why_now": attrs.get("why_now"),
                        "recommended_service": attrs.get("recommended_service"),
                    },
                    "buying_signals": attrs.get("buying_signals") or [],
                }
                snap = self.pipeline.evaluate(
                    site_payload,
                    fetch_github=False,
                    recover_contacts=need_email,
                    recover_dms=need_dm,
                    crawl_website=need_email or need_dm,
                    company_id=str(company.id),
                )
                emails = list(snap.emails)
                dms = list(snap.decision_makers)
                if not emails and (attrs.get("business_email") or attrs.get("ofc_business_email")):
                    existing_email = str(attrs.get("business_email") or attrs.get("ofc_business_email"))
                    from revenue_data_acquisition.models.types import AttributedValue

                    emails = [
                        AttributedValue(
                            value=existing_email,
                            source="company_attributes",
                            collector=source,
                            confidence=90.0,
                            verified=True,
                            evidence=["persisted_attribute"],
                        )
                    ]
                if not dms and attrs.get("decision_maker"):
                    raw_dm = str(attrs["decision_maker"])
                    name, role = raw_dm, "unknown"
                    if "(" in raw_dm and raw_dm.endswith(")"):
                        name = raw_dm.rsplit("(", 1)[0].strip()
                        role = raw_dm.rsplit("(", 1)[1][:-1].strip() or "unknown"
                    dms = [
                        {
                            "name": name,
                            "role": role,
                            "url": f"{website}/about",
                            "confidence": 80.0,
                            "source": "company_attributes",
                            "collector": source,
                        }
                    ]
                if need_email and snap.emails:
                    email = snap.emails[0].value
                    attrs["business_email"] = email
                    attrs["ofc_business_email"] = email
                    self.session.add(
                        RdapContactRecovery(
                            id=uuid.uuid4(),
                            company_id=company.id,
                            domain=company.primary_domain,
                            email=email,
                            confidence=snap.emails[0].confidence,
                            source=snap.emails[0].source,
                            collector=source,
                            payload=snap.emails[0].model_dump(mode="json"),
                        )
                    )
                if need_dm and snap.decision_makers:
                    dm = snap.decision_makers[0]
                    attrs["decision_maker"] = f"{dm.get('name')} ({dm.get('role')})"
                    self.session.add(
                        RdapDmRecovery(
                            id=uuid.uuid4(),
                            company_id=company.id,
                            domain=company.primary_domain,
                            name=str(dm.get("name") or "unknown"),
                            role=dm.get("role"),
                            confidence=float(dm.get("confidence") or 0),
                            evidence_url=dm.get("url"),
                            payload=dm,
                        )
                    )
                # Rebuild dossier with recovered + existing attributed contacts
                dossier = self.pipeline.dossier.build(
                    company_id=str(company.id),
                    identity=snap.payload.get("identity") or {"trade_name": company.name},
                    website=website,
                    domain=company.primary_domain,
                    emails=emails,
                    decision_makers=dms,
                    payload=site_payload,
                    collector=source,
                )
                snap = snap.model_copy(update={"dossier": dossier, "emails": emails, "decision_makers": dms})
                if snap.dossier:
                    attrs["rdap_dossier"] = snap.dossier.model_dump(mode="json")
                    attrs["rdap_sales_ready"] = snap.dossier.sales_ready
                    attrs["rdap_revenue_ready"] = snap.dossier.revenue_ready
                    attrs["rdap_trust_score"] = snap.dossier.trust_score
                    self.session.add(
                        RdapCompanyProfile(
                            id=uuid.uuid4(),
                            company_id=company.id,
                            domain=company.primary_domain,
                            website=website,
                            trust_score=snap.dossier.trust_score,
                            sales_ready=snap.dossier.sales_ready,
                            revenue_ready=snap.dossier.revenue_ready,
                            dossier=snap.dossier.model_dump(mode="json"),
                            payload={"source": source},
                            scoring_version="rdap-v1",
                        )
                    )
                    if snap.dossier.revenue_ready or (
                        snap.dossier.sales_ready and len(top_rr) < 10
                    ):
                        top_rr.append(
                            {
                                "company_id": str(company.id),
                                "name": company.name,
                                "domain": company.primary_domain,
                                "website": website,
                                "email": attrs.get("business_email"),
                                "decision_maker": attrs.get("decision_maker"),
                                "sales_ready": snap.dossier.sales_ready,
                                "revenue_ready": snap.dossier.revenue_ready,
                                "trust_score": snap.dossier.trust_score,
                                "evidence": snap.dossier.evidence_timeline[:6],
                            }
                        )
                attrs["rdap_recovered_at"] = datetime.now(UTC).isoformat()
                company.attributes = attrs
                flag_modified(company, "attributes")

                for row in collector_rows:
                    if row.get("connector") == source and row.get("website"):
                        if attrs.get("business_email"):
                            row["business_email"] = attrs["business_email"]
                        if attrs.get("decision_maker"):
                            row["decision_maker"] = attrs["decision_maker"]
                        if attrs.get("rdap_sales_ready"):
                            row["sales_ready"] = True
                        if attrs.get("rdap_revenue_ready"):
                            row["revenue_ready"] = True

        after = await self._live_kpis()
        after["signals"] = len(events)
        after["companies_created"] = created
        after["github_live_fetches"] = gh_fetches
        after["companies_crawled"] = crawled

        # Append one row per verified company for honest connector yield analytics
        for company in companies:
            attrs = company.attributes or {}
            collector_rows.append(
                {
                    "connector": str(attrs.get("source") or "unknown"),
                    "candidate": True,
                    "company": True,
                    "verified_company": True,
                    "website": bool(company.primary_domain),
                    "business_email": bool(attrs.get("business_email") or attrs.get("ofc_business_email")),
                    "decision_maker": bool(attrs.get("decision_maker")),
                    "sales_ready": bool(attrs.get("rdap_sales_ready")),
                    "revenue_ready": bool(attrs.get("rdap_revenue_ready")),
                    "confidence": float(attrs.get("rdap_trust_score") or 70),
                    "duplicate": 0,
                }
            )

        audit = self.rebuild.audit(
            before=before,
            after=after,
            snaps=snaps,
            collector_rows=collector_rows,
            top_rr=sorted(top_rr, key=lambda x: (x.get("revenue_ready"), x.get("trust_score")), reverse=True)[:10],
        )

        role_counts: dict[str, int] = {}
        for event in events:
            role_counts[event.source] = role_counts.get(event.source, 0) + 1
        for connector, count in role_counts.items():
            self.session.add(
                RdapSourceMetric(
                    id=uuid.uuid4(),
                    connector=connector,
                    roles=[r.value for r in self.roles.roles(connector)],
                    signals=count,
                    payload={"roles": [r.value for r in self.roles.roles(connector)]},
                )
            )
        for c in audit.connectors:
            self.session.add(
                RdapConnectorScore(
                    id=uuid.uuid4(),
                    connector=c.connector,
                    grade=c.grade.value,
                    verified_companies=c.verified_companies,
                    business_emails=c.business_emails,
                    decision_makers=c.decision_makers,
                    revenue_ready=c.revenue_ready,
                    revenue_yield=c.revenue_yield,
                    payload=c.model_dump(mode="json"),
                )
            )
        for y in audit.yields:
            self.session.add(
                RdapRevenueYield(
                    id=uuid.uuid4(),
                    connector=y.connector,
                    signals=y.signals,
                    companies=y.companies,
                    emails=y.emails,
                    decision_makers=y.decision_makers,
                    revenue_ready=y.revenue_ready,
                    yield_pct=y.yield_pct,
                    payload=y.model_dump(mode="json"),
                )
            )
        self.session.add(
            RdapDailyReport(
                id=uuid.uuid4(),
                payload=audit.model_dump(mode="json"),
                verified_companies=after["verified_companies"],
                business_emails=after["business_emails"],
                decision_makers=after["decision_makers"],
                sales_ready=after["sales_ready"],
                revenue_ready=after["revenue_ready"],
                vansh_ready_answer=audit.vansh_ready_answer,
                scoring_version="rdap-v1",
            )
        )
        await self.session.commit()
        return {
            "before": before,
            "after": after,
            "audit": audit.model_dump(mode="json"),
            "created": created,
            "github_live_fetches": gh_fetches,
            "companies_crawled": crawled,
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
        sales = sum(1 for c in with_domain if (c.attributes or {}).get("rdap_sales_ready"))
        rr = sum(1 for c in with_domain if (c.attributes or {}).get("rdap_revenue_ready"))
        # Outreach-ready: website + email + named DM (independent of full REV gate)
        outreach = sum(
            1
            for c in with_domain
            if (
                ((c.attributes or {}).get("business_email") or (c.attributes or {}).get("ofc_business_email"))
                and (c.attributes or {}).get("decision_maker")
            )
        )
        return {
            "companies": len(companies),
            "verified_companies": len(with_domain),
            "official_websites": len(with_domain),
            "business_emails": emails,
            "decision_makers": dms,
            "sales_ready": sales,
            "revenue_ready": rr,
            "outreach_ready": outreach,
        }
