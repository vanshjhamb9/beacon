from __future__ import annotations

import os
import uuid
from collections import Counter, defaultdict
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.models.dataset_unlock import (
    OduConnectorHealth,
    OduConnectorMetric,
    OduDailyReport,
    OduOperationLog,
    OduRecoveryQueue,
    OduSourceToken,
)
from app.models.intelligence import Company
from app.models.raw_event import RawEvent
from app.services.identity_graph import IdentityGraphService
from app.services.revenue_data_acquisition import RevenueDataAcquisitionService
from dataset_unlock.pipelines.engine import DatasetUnlockPipeline
from identity_graph.pipelines.engine import IdentityResolutionPipeline
from revenue_data_acquisition.contact_recovery.engine import ContactRecoveryEngine
from revenue_data_acquisition.dm_recovery.engine import DecisionMakerRecoveryEngine
from revenue_data_acquisition.dossier.engine import CompanyDossierEngine
from revenue_data_acquisition.models.types import AttributedValue


class DatasetUnlockService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.pipeline = DatasetUnlockPipeline()
        self.igf = IdentityResolutionPipeline()
        self.igf_service = IdentityGraphService(session)
        self.rdap = RevenueDataAcquisitionService(session)
        self.contacts = ContactRecoveryEngine()
        self.dms = DecisionMakerRecoveryEngine()
        self.dossier = CompanyDossierEngine()

    async def health(self) -> dict[str, Any]:
        return {"connectors": self.pipeline.connector_health(), "scoring_version": "odu-v1"}

    async def connectors(self) -> dict[str, Any]:
        rows = (
            await self.session.execute(
                select(OduConnectorMetric)
                .where(OduConnectorMetric.deleted_at.is_(None))
                .order_by(OduConnectorMetric.created_at.desc())
                .limit(40)
            )
        ).scalars().all()
        return {
            "items": [
                {
                    "connector": r.connector,
                    "signals": r.signals,
                    "websites": r.websites,
                    "companies": r.companies,
                    "emails": r.emails,
                    "decision_makers": r.decision_makers,
                    "revenue_ready": r.revenue_ready,
                    "yield_pct": r.yield_pct,
                    **(r.payload or {}),
                }
                for r in rows
            ],
            "health": self.pipeline.connector_health(),
        }

    async def recovery(self, *, limit: int = 50) -> dict[str, Any]:
        rows = (
            await self.session.execute(
                select(OduRecoveryQueue)
                .where(OduRecoveryQueue.deleted_at.is_(None), OduRecoveryQueue.status == "pending")
                .order_by(OduRecoveryQueue.created_at.desc())
                .limit(limit)
            )
        ).scalars().all()
        return {
            "items": [
                {
                    "id": str(r.id),
                    "domain": r.domain,
                    "reason": r.reason,
                    "status": r.status,
                    "attempts": r.attempts,
                }
                for r in rows
            ],
            "count": len(rows),
        }

    async def report(self) -> dict[str, Any]:
        latest = (
            await self.session.execute(
                select(OduDailyReport)
                .where(OduDailyReport.deleted_at.is_(None))
                .order_by(OduDailyReport.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if not latest:
            kpis = await self._live_kpis()
            return {"status": "empty", "kpis": kpis}
        return {
            "id": str(latest.id),
            "vansh_ready_answer": latest.vansh_ready_answer,
            "verified_companies": latest.verified_companies,
            "business_emails": latest.business_emails,
            "decision_makers": latest.decision_makers,
            "sales_ready": latest.sales_ready,
            "revenue_ready": latest.revenue_ready,
            "payload": latest.payload,
            "created_at": latest.created_at.isoformat() if latest.created_at else None,
        }

    async def dashboard(self) -> dict[str, Any]:
        kpis = await self._live_kpis()
        latest = await self.report()
        payload = (latest.get("payload") or {}) if latest.get("status") != "empty" else {}
        recovery = await self.recovery(limit=20)
        return {
            "scoring_version": "odu-v1",
            "kpis": kpis,
            "funnel_identity": [
                {"name": "Signals", "count": kpis.get("signals") or 0},
                {"name": "Identity Candidates", "count": payload.get("identity_candidates") or kpis["verified_companies"]},
                {"name": "Verified Websites", "count": kpis["official_websites"]},
                {"name": "Verified Companies", "count": kpis["verified_companies"]},
            ],
            "funnel_contacts": [
                {"name": "Companies", "count": kpis["verified_companies"]},
                {"name": "Emails", "count": kpis["business_emails"]},
                {"name": "Decision Makers", "count": kpis["decision_makers"]},
                {"name": "Sales Ready", "count": kpis["sales_ready"]},
                {"name": "Revenue Ready", "count": kpis["revenue_ready"]},
            ],
            "connectors": (await self.connectors()).get("items") or [],
            "source_health": self.pipeline.connector_health(),
            "recovery": recovery,
            "top_companies": payload.get("top_companies") or [],
            "top_failures": payload.get("top_failures") or {},
            "vansh_ready_answer": latest.get("vansh_ready_answer") or "NO",
            "audit_answers": payload.get("audit_answers") or {},
        }

    async def unlock(
        self,
        *,
        collect_new: bool = True,
        recover_contacts: bool = True,
        recover_dms: bool = True,
        company_crawl_cap: int = 160,
        github_fetch_cap: int = 40,
    ) -> dict[str, Any]:
        before = await self._live_kpis()
        failures: Counter[str] = Counter()
        connector_stats: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        websites_recovered = 0
        emails_recovered = 0
        dms_recovered = 0
        created = 0
        existing = await self.igf_service._existing_canonical()

        events_payloads: list[dict[str, Any]] = []

        if collect_new:
            for ev in self.pipeline.collect_identity_events():
                # Defense in depth — never persist directory rows as lead events
                meta = dict(ev.metadata or {})
                if meta.get("lead_eligible") is False or meta.get("source_kind") == "directory":
                    continue
                events_payloads.append(
                    {
                        "signal_id": ev.idempotency_key[:32],
                        "title": ev.title,
                        "body": ev.content,
                        "content": ev.content,
                        "url": ev.url,
                        "source": ev.source,
                        "metadata": meta,
                        "official_website": meta.get("official_website"),
                        "published_at": ev.published_at,
                        "raw_event": ev,
                    }
                )

        # Re-enrich PH (token) + GitHub signals that still lack websites
        raw_events = (
            await self.session.execute(
                select(RawEvent)
                .where(
                    RawEvent.deleted_at.is_(None),
                    RawEvent.source.in_(["product_hunt", "github_trending"]),
                )
                .order_by(RawEvent.created_at.desc())
                .limit(200)
            )
        ).scalars().all()
        gh_fetches = 0
        for event in raw_events:
            meta = dict(getattr(event, "event_metadata", None) or {})
            if meta.get("official_website") or meta.get("domain"):
                continue
            payload = {
                "signal_id": str(event.id),
                "title": event.title or "",
                "body": event.content or "",
                "content": event.content or "",
                "url": event.url,
                "source": event.source,
                "metadata": meta,
                "official_website": meta.get("homepage") or meta.get("repo_homepage"),
            }
            if event.source == "github_trending" and gh_fetches < github_fetch_cap:
                payload = self.pipeline.enrich_github_payload(payload, fetch_live=True)
                gh_fetches += 1
                if not (payload.get("official_website") or (payload.get("metadata") or {}).get("official_website")):
                    continue
            elif event.source == "product_hunt" and self.pipeline.ph.has_token:
                from identity_coverage.product_hunt.engine import ProductHuntApiResolver

                for ce in ProductHuntApiResolver().collect(payload):
                    if ce.field == "website":
                        payload["official_website"] = ce.value
                        payload["metadata"]["official_website"] = ce.value
                    if ce.field == "official_domain":
                        payload["metadata"]["official_domain"] = ce.value
                        payload["metadata"]["domain"] = ce.value
                if not payload.get("official_website"):
                    continue
            else:
                continue
            events_payloads.append(payload)

        identity_candidates = 0
        for payload in events_payloads:
            source = str(payload.get("source") or "unknown")
            connector_stats[source]["signals"] += 1
            meta = dict(payload.get("metadata") or {})
            website = payload.get("official_website") or meta.get("official_website")
            domain = meta.get("official_domain") or meta.get("domain")
            if website and not domain:
                domain = website.replace("https://", "").replace("http://", "").split("/")[0].removeprefix("www.")
            if not website or not domain:
                failures["Missing Website"] += 1
                if source == "product_hunt" and not self.pipeline.ph.has_token:
                    failures["Missing Token"] += 1
                    failures["Cloudflare"] += 1
                continue

            attr_conf = float((meta.get("website_attribution") or {}).get("confidence") or 0)
            if attr_conf >= 94.0 and domain:
                # High-confidence attributed identity sources (YC / App Store / PH GraphQL)
                verification = {
                    "verified": True,
                    "confidence": attr_conf,
                    "status": "verified",
                    "domain": domain,
                    "website": website,
                    "checks": {"attributed_source": True},
                }
            else:
                verification = self.pipeline.verify_website(
                    str(website), company_name=str(payload.get("title") or "")
                )
            if not verification.get("verified") and verification.get("status") != "identity_candidate":
                failures["Missing Website"] += 1
                continue
            websites_recovered += 1
            connector_stats[source]["websites"] += 1
            identity_candidates += 1

            # Persist raw event for new collectors
            raw_ev = payload.get("raw_event")
            raw_event_id = None
            if raw_ev is not None:
                existing_raw = (
                    await self.session.execute(
                        select(RawEvent).where(RawEvent.event_hash == raw_ev.event_hash).limit(1)
                    )
                ).scalar_one_or_none()
                if existing_raw:
                    raw_event_id = existing_raw.id
                else:
                    raw_event_id = uuid.uuid4()
                    self.session.add(
                        RawEvent(
                            id=raw_event_id,
                            source=raw_ev.source,
                            url=raw_ev.url,
                            title=raw_ev.title,
                            content=raw_ev.content,
                            published_at=raw_ev.published_at,
                            event_metadata=meta,
                            event_hash=raw_ev.event_hash,
                            idempotency_key=raw_ev.idempotency_key,
                        )
                    )
                    await self.session.flush()

            enriched = {
                **payload,
                "official_website": website,
                "homepage": website,
                "official_domain": domain,
                "domain": domain,
                "metadata": {
                    **meta,
                    "official_website": website,
                    "official_domain": domain,
                    "domain": domain,
                    "odu_verified": verification,
                },
                "business_email": meta.get("business_email"),
                "decision_maker": meta.get("decision_maker"),
                "description": meta.get("description"),
                "buying_signals": meta.get("buying_signals") or [],
            }
            igf_snap = self.igf.evaluate(enriched, existing=existing)
            company_id = None
            if igf_snap.admission.allow_create_company and igf_snap.domain and igf_snap.canonical:
                try:
                    company_id = await self.igf_service._upsert_company(igf_snap)
                    if company_id:
                        await self.session.flush()
                except IntegrityError:
                    await self.session.rollback()
                    existing = await self.igf_service._existing_canonical()
                    failures["Duplicate"] += 1
                    connector_stats[source]["duplicates"] += 1
                    company_id = None
                if company_id:
                    created += 1
                    connector_stats[source]["companies"] += 1
                    existing.append(
                        {
                            "id": str(company_id),
                            "official_domain": igf_snap.domain,
                            "trade_name": igf_snap.canonical.trade_name,
                            "legal_name": igf_snap.canonical.legal_name,
                            "aliases": igf_snap.canonical.aliases,
                        }
                    )
                    company = await self.session.get(Company, company_id)
                    if company:
                        attrs = dict(company.attributes or {})
                        attrs["source"] = source
                        if meta.get("business_email") and not attrs.get("business_email"):
                            attrs["business_email"] = meta["business_email"]
                            attrs["ofc_business_email"] = meta["business_email"]
                        if meta.get("decision_maker") and not attrs.get("decision_maker"):
                            attrs["decision_maker"] = meta["decision_maker"]
                            attrs["decision_makers"] = meta.get("decision_makers") or []
                        if meta.get("buying_signals"):
                            attrs["buying_signals"] = meta["buying_signals"]
                        attrs["odu_unlocked_at"] = datetime.now(UTC).isoformat()
                        company.attributes = attrs
                        flag_modified(company, "attributes")
            elif igf_snap.merge.merged:
                failures["Duplicate"] += 1
                connector_stats[source]["duplicates"] += 1
            else:
                failures["Identity Conflict"] += 1
                self.session.add(
                    OduRecoveryQueue(
                        id=uuid.uuid4(),
                        reason="Identity Conflict",
                        domain=domain,
                        status="pending",
                        payload={"source": source, "title": payload.get("title")},
                    )
                )

            try:
                await self.igf_service.persist_run(
                    igf_snap.model_dump(mode="json"),
                    raw_event_id=raw_event_id,
                    company_id=company_id,
                    commit=False,
                )
            except IntegrityError:
                await self.session.rollback()
                existing = await self.igf_service._existing_canonical()
                failures["Duplicate"] += 1

            if created and created % 15 == 0:
                await self.session.commit()
                existing = await self.igf_service._existing_canonical()

        # Contact + DM recovery — prioritize missing fields; cap live HTTP work
        companies = (
            await self.session.execute(
                select(Company).where(Company.deleted_at.is_(None), Company.primary_domain.is_not(None))
            )
        ).scalars().all()
        top_companies: list[dict[str, Any]] = []
        email_budget = min(60, company_crawl_cap)
        dm_budget = min(40, company_crawl_cap)
        email_attempts = 0
        dm_attempts = 0
        for company in companies:
            attrs = dict(company.attributes or {})
            website = f"https://{company.primary_domain}"
            source = str(attrs.get("source") or "official_website")
            need_email = recover_contacts and not (attrs.get("business_email") or attrs.get("ofc_business_email"))
            need_dm = recover_dms and not attrs.get("decision_maker")

            if need_email and email_attempts < email_budget:
                email_attempts += 1
                emails = self.contacts.recover(website, collector=source, timeout=4.0)
                if emails:
                    attrs["business_email"] = emails[0].value
                    attrs["ofc_business_email"] = emails[0].value
                    emails_recovered += 1
                else:
                    failures["No Email"] += 1
                    self.session.add(
                        OduRecoveryQueue(
                            id=uuid.uuid4(),
                            company_id=company.id,
                            domain=company.primary_domain,
                            reason="Email Missing",
                            status="pending",
                            payload={},
                        )
                    )
            elif need_email:
                failures["No Email"] += 1

            if need_dm:
                if attrs.get("decision_makers"):
                    dm0 = attrs["decision_makers"][0]
                    if isinstance(dm0, dict) and dm0.get("name"):
                        attrs["decision_maker"] = f"{dm0['name']} ({dm0.get('role') or 'Founder'})"
                        dms_recovered += 1
                        need_dm = False
                if need_dm and dm_attempts < dm_budget:
                    dm_attempts += 1
                    people = self.dms.recover(website, collector=source, timeout=4.0)
                    if people:
                        attrs["decision_maker"] = f"{people[0]['name']} ({people[0].get('role')})"
                        attrs["decision_makers"] = people
                        dms_recovered += 1
                    else:
                        failures["No DM"] += 1
                        self.session.add(
                            OduRecoveryQueue(
                                id=uuid.uuid4(),
                                company_id=company.id,
                                domain=company.primary_domain,
                                reason="DM Missing",
                                status="pending",
                                payload={},
                            )
                        )
                elif need_dm:
                    failures["No DM"] += 1

            email_val = attrs.get("business_email") or attrs.get("ofc_business_email")
            emails_attr = (
                [AttributedValue(value=str(email_val), source="company", confidence=90, verified=True)]
                if email_val
                else []
            )
            dms_attr = []
            if attrs.get("decision_maker"):
                raw = str(attrs["decision_maker"])
                name, role = raw, "unknown"
                if "(" in raw and raw.endswith(")"):
                    name = raw.rsplit("(", 1)[0].strip()
                    role = raw.rsplit("(", 1)[1][:-1]
                dms_attr = [{"name": name, "role": role, "url": f"{website}/about", "confidence": 85}]

            dossier = self.dossier.build(
                company_id=str(company.id),
                identity={"trade_name": company.name, "legal_name": company.name},
                website=website,
                domain=company.primary_domain,
                emails=emails_attr,
                decision_makers=dms_attr,
                payload={
                    "title": company.name,
                    "source": source,
                    "metadata": {
                        "buying_signals": attrs.get("buying_signals") or [],
                        "why_now": attrs.get("why_now"),
                    },
                },
                collector=source,
            )
            attrs["rdap_sales_ready"] = dossier.sales_ready
            attrs["rdap_revenue_ready"] = dossier.revenue_ready
            attrs["rdap_trust_score"] = dossier.trust_score
            attrs["rdap_dossier"] = dossier.model_dump(mode="json")
            attrs["odu_recovered_at"] = datetime.now(UTC).isoformat()
            company.attributes = attrs
            flag_modified(company, "attributes")

            if email_val:
                connector_stats[source]["emails"] += 1
            if attrs.get("decision_maker"):
                connector_stats[source]["decision_makers"] += 1
            if dossier.sales_ready:
                connector_stats[source]["sales_ready"] += 1
            if dossier.revenue_ready:
                connector_stats[source]["revenue_ready"] += 1

            if dossier.sales_ready or dossier.revenue_ready or (email_val and attrs.get("decision_maker")):
                top_companies.append(
                    {
                        "company": company.name,
                        "website": website,
                        "email": email_val,
                        "decision_maker": attrs.get("decision_maker"),
                        "why_today": (attrs.get("buying_signals") or ["Verified identity unlock"])[0],
                        "evidence": dossier.evidence_timeline[:5],
                        "revenue_ready": dossier.revenue_ready,
                        "sales_ready": dossier.sales_ready,
                    }
                )

        after = await self._live_kpis()
        after["companies_created"] = created
        after["github_live_fetches"] = gh_fetches
        after["identity_candidates"] = identity_candidates

        health_rows = self.pipeline.connector_health()
        health_by = {h["connector"]: h for h in health_rows}
        connector_rows = []
        for connector, stats in connector_stats.items():
            h = health_by.get(connector, {})
            connector_rows.append(
                {
                    "connector": connector,
                    "signals": stats["signals"],
                    "websites": stats["websites"],
                    "companies": stats["companies"],
                    "emails": stats["emails"],
                    "decision_makers": stats["decision_makers"],
                    "sales_ready": stats["sales_ready"],
                    "revenue_ready": stats["revenue_ready"],
                    "duplicates": stats["duplicates"],
                    "health": h.get("health"),
                    "note": h.get("note"),
                }
            )

        audit = self.pipeline.build_audit(
            before=before,
            after=after,
            connector_rows=connector_rows,
            top_companies=sorted(
                top_companies, key=lambda x: (x.get("revenue_ready"), x.get("sales_ready")), reverse=True
            ),
            failures=dict(failures),
            websites_recovered=websites_recovered,
            emails_recovered=emails_recovered,
            dms_recovered=dms_recovered,
        )
        audit_payload = audit.model_dump(mode="json")
        audit_payload["identity_candidates"] = identity_candidates
        audit_payload["audit_answers"] = {
            "official_websites_recovered": websites_recovered,
            "highest_revenue_yield_connector": audit.highest_yield_connector,
            "disable_connectors": audit.disable_connectors,
            "business_emails_recovered": emails_recovered,
            "decision_makers_recovered": dms_recovered,
            "sales_ready": after.get("sales_ready"),
            "revenue_ready": after.get("revenue_ready"),
            "vansh_contact_10": audit.vansh_ready_answer,
        }

        for h in health_rows:
            self.session.add(
                OduConnectorHealth(
                    id=uuid.uuid4(),
                    connector=h["connector"],
                    health=h["health"],
                    note=h.get("note"),
                    payload=h,
                )
            )
        for key, env_key in (
            ("product_hunt", "PRODUCT_HUNT_DEVELOPER_TOKEN"),
            ("github", "GITHUB_TOKEN"),
            ("crunchbase", "CRUNCHBASE_API_KEY"),
            ("apollo", "APOLLO_API_KEY"),
            ("people_data_labs", "PEOPLE_DATA_LABS_API_KEY"),
        ):
            self.session.add(
                OduSourceToken(
                    id=uuid.uuid4(),
                    provider=key,
                    present=bool(os.getenv(env_key)),
                    env_key=env_key,
                    payload={},
                )
            )
        for row in connector_rows:
            self.session.add(
                OduConnectorMetric(
                    id=uuid.uuid4(),
                    connector=row["connector"],
                    signals=row["signals"],
                    websites=row["websites"],
                    companies=row["companies"],
                    emails=row["emails"],
                    decision_makers=row["decision_makers"],
                    revenue_ready=row["revenue_ready"],
                    yield_pct=round(
                        (row["revenue_ready"] / row["signals"] * 100.0) if row["signals"] else 0.0, 2
                    ),
                    payload=row,
                )
            )
        self.session.add(
            OduDailyReport(
                id=uuid.uuid4(),
                payload=audit_payload,
                verified_companies=after["verified_companies"],
                business_emails=after["business_emails"],
                decision_makers=after["decision_makers"],
                sales_ready=after["sales_ready"],
                revenue_ready=after["revenue_ready"],
                vansh_ready_answer=audit.vansh_ready_answer,
                scoring_version="odu-v1",
            )
        )
        self.session.add(
            OduOperationLog(
                id=uuid.uuid4(),
                operation="unlock",
                message=f"ODU unlock created={created} websites={websites_recovered} answer={audit.vansh_ready_answer}",
                payload={"before": before, "after": after},
            )
        )
        await self.session.commit()
        return {
            "before": before,
            "after": after,
            "audit": audit_payload,
            "created": created,
            "websites_recovered": websites_recovered,
            "emails_recovered": emails_recovered,
            "dms_recovered": dms_recovered,
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
        outreach = sum(
            1
            for c in with_domain
            if (
                ((c.attributes or {}).get("business_email") or (c.attributes or {}).get("ofc_business_email"))
                and (c.attributes or {}).get("decision_maker")
            )
        )
        signals = (
            await self.session.execute(select(func.count()).select_from(RawEvent).where(RawEvent.deleted_at.is_(None)))
        ).scalar() or 0
        return {
            "signals": int(signals),
            "companies": len(companies),
            "verified_companies": len(with_domain),
            "official_websites": len(with_domain),
            "business_emails": emails,
            "decision_makers": dms,
            "sales_ready": sales,
            "revenue_ready": rr,
            "outreach_ready": outreach,
        }
