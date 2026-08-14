from __future__ import annotations

import uuid
from collections import Counter
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.models.intelligence import Company
from app.models.revenue_readiness_perfection import RrpCompanyProfile, RrpDailyReport, RrpFounderReview
from revenue_readiness_perfection.models.types import ContactCategory, FounderReviewLabel
from revenue_readiness_perfection.pipelines.engine import RevenueReadinessPerfectionPipeline


class RevenueReadinessPerfectionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.pipeline = RevenueReadinessPerfectionPipeline()

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
        dm_emails = sum(
            1
            for c in with_domain
            if (c.attributes or {}).get("rrp_decision_maker_email")
        )
        # Contact method = named DM + usable outreach email (business/sales/support/DM).
        # Public personal DM inboxes are rare; this is what Founder Queue uses to start outreach.
        dm_contact_methods = sum(
            1
            for c in with_domain
            if (
                ((c.attributes or {}).get("rrp_revenue_ready") or (c.attributes or {}).get("rdap_revenue_ready"))
                and (c.attributes or {}).get("decision_maker")
                and (
                    (c.attributes or {}).get("rrp_decision_maker_email")
                    or (c.attributes or {}).get("business_email")
                    or (c.attributes or {}).get("ofc_business_email")
                )
            )
        )
        sales = sum(1 for c in with_domain if (c.attributes or {}).get("rdap_sales_ready"))
        rr = sum(1 for c in with_domain if (c.attributes or {}).get("rdap_revenue_ready") or (c.attributes or {}).get("rrp_revenue_ready"))
        conf90 = sum(1 for c in with_domain if float((c.attributes or {}).get("rrp_confidence") or 0) >= 90)
        trust95 = sum(1 for c in with_domain if float((c.attributes or {}).get("rrp_trust") or 0) >= 95)
        return {
            "verified_companies": len(with_domain),
            "business_emails": emails,
            "decision_makers": dms,
            "decision_maker_emails": dm_emails,
            "decision_maker_contact_methods": dm_contact_methods,
            "sales_ready": sales,
            "revenue_ready": rr,
            "confidence_ge_90": conf90,
            "trust_ge_95": trust95,
        }

    async def dashboard(self) -> dict[str, Any]:
        kpis = await self._live_kpis()
        latest = (
            await self.session.execute(
                select(RrpDailyReport)
                .where(RrpDailyReport.deleted_at.is_(None))
                .order_by(RrpDailyReport.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        payload = dict(latest.payload) if latest else {}
        return {
            "scoring_version": "rrp-v1",
            "kpis": kpis,
            "funnel": [
                {"name": "Verified Companies", "count": kpis["verified_companies"]},
                {"name": "Business Emails", "count": kpis["business_emails"]},
                {"name": "Decision Makers", "count": kpis["decision_makers"]},
                {"name": "Sales Ready", "count": kpis["sales_ready"]},
                {"name": "Revenue Ready", "count": kpis["revenue_ready"]},
            ],
            "blockers": payload.get("blocker_counts") or {},
            "top_10": payload.get("top_10") or [],
            "vansh_ready_answer": latest.vansh_ready_answer if latest else "NO",
            "promoted": payload.get("promoted") or [],
            "still_blocked": payload.get("still_blocked") or [],
        }

    async def founder_queue_v4(self) -> dict[str, Any]:
        from collectors.freshness import (
            DIRECTORY_SOURCES,
            FRESH_HOURS,
            cutoff_datetime,
            why_now_is_stale,
        )

        dash = await self.dashboard()
        items = dash.get("top_10") or []
        cutoff = cutoff_datetime(max_age_hours=FRESH_HOURS)

        def _fresh_item(item: dict[str, Any], company: Company | None = None) -> bool:
            source = str(item.get("source") or (company.attributes or {}).get("source") or "").lower()
            if source in DIRECTORY_SOURCES:
                return False
            why = str(item.get("why_now") or "")
            if why_now_is_stale(why) or "insufficient why-now" in why.lower():
                return False
            # Prefer explicit content time; fall back to company last_seen / profile stamps
            for key in ("content_occurred_at", "launch_date", "published_at", "last_verified", "updated_at"):
                raw = item.get(key)
                if not raw and company is not None and key == "updated_at":
                    raw = company.last_seen_at or company.updated_at
                if raw is None:
                    continue
                try:
                    from collectors.freshness import parse_datetime

                    dt = parse_datetime(raw)
                    if dt is not None:
                        return dt >= cutoff
                except Exception:  # noqa: BLE001
                    continue
            if company is not None and company.last_seen_at is not None:
                seen = company.last_seen_at
                if seen.tzinfo is None:
                    from datetime import UTC

                    seen = seen.replace(tzinfo=UTC)
                return seen >= cutoff
            return False

        if not items:
            # fallback from company attrs — still enforce freshness
            companies = (
                await self.session.execute(select(Company).where(Company.deleted_at.is_(None)))
            ).scalars().all()
            ready = [
                c
                for c in companies
                if (c.attributes or {}).get("rrp_revenue_ready")
                or (c.attributes or {}).get("rdap_revenue_ready")
                or (c.attributes or {}).get("perfect_lead")
                or (c.attributes or {}).get("outbound_ready")
                or float((c.attributes or {}).get("lead_quality_score") or 0) >= 78
            ]
            items = []
            for c in ready:
                a = c.attributes or {}
                opp = a.get("rrp_opportunity") or {}
                dm = a.get("rrp_decision_maker") or {}
                row = {
                    "company_id": str(c.id),
                    "company": c.name,
                    "logo": None,
                    "website": f"https://{c.primary_domain}" if c.primary_domain else None,
                    "decision_maker": dm.get("full_name") or a.get("decision_maker"),
                    "decision_maker_email": a.get("rrp_decision_maker_email"),
                    "business_email": a.get("business_email") or a.get("ofc_business_email"),
                    "why_now": a.get("rrp_why_now") or opp.get("why_now"),
                    "recommended_service": opp.get("recommended_service"),
                    "confidence": a.get("rrp_confidence") or a.get("lead_quality_score"),
                    "revenue_ready": True,
                    "last_verified": dm.get("last_verified"),
                    "evidence_count": len(opp.get("evidence") or a.get("buying_signals") or []),
                    "source": a.get("source"),
                    "content_occurred_at": a.get("content_occurred_at") or a.get("launch_date"),
                    "buying_signals": a.get("buying_signals") or [],
                }
                if _fresh_item(row, c):
                    items.append(row)
        else:
            filtered: list[dict[str, Any]] = []
            for item in items:
                cid = item.get("company_id")
                company = None
                if cid:
                    try:
                        from uuid import UUID

                        company = await self.session.get(Company, UUID(str(cid)))
                    except Exception:  # noqa: BLE001
                        company = None
                if _fresh_item(item, company):
                    filtered.append(item)
            items = filtered
            # If dashboard top_10 was all stale, fall back to persisted fresh LQS leads
            if not items:
                companies = (
                    await self.session.execute(select(Company).where(Company.deleted_at.is_(None)))
                ).scalars().all()
                for c in companies:
                    a = c.attributes or {}
                    if not (
                        a.get("perfect_lead")
                        or a.get("rrp_revenue_ready")
                        or float(a.get("lead_quality_score") or 0) >= 78
                    ):
                        continue
                    row = {
                        "company_id": str(c.id),
                        "company": c.name,
                        "logo": None,
                        "website": f"https://{c.primary_domain}" if c.primary_domain else None,
                        "decision_maker": a.get("decision_maker"),
                        "decision_maker_email": a.get("rrp_decision_maker_email"),
                        "business_email": a.get("business_email") or a.get("ofc_business_email"),
                        "why_now": a.get("rrp_why_now"),
                        "recommended_service": (a.get("rrp_opportunity") or {}).get("recommended_service"),
                        "confidence": a.get("lead_quality_score") or a.get("rrp_confidence"),
                        "revenue_ready": True,
                        "last_verified": None,
                        "evidence_count": len(a.get("buying_signals") or []),
                        "source": a.get("source"),
                        "content_occurred_at": a.get("content_occurred_at"),
                        "buying_signals": a.get("buying_signals") or [],
                    }
                    if _fresh_item(row, c):
                        items.append(row)

        from lead_quality import OUTBOUND_THRESHOLD, PERFECT_THRESHOLD, LeadQualityScorer, SCORING_VERSION

        scorer = LeadQualityScorer()
        ranked: list[dict[str, Any]] = []
        for item in items:
            payload = {
                "company_name": item.get("company"),
                "source": item.get("source"),
                "website": item.get("website"),
                "official_website": item.get("website"),
                "business_email": item.get("business_email") or item.get("decision_maker_email"),
                "decision_maker": item.get("decision_maker"),
                "why_now": item.get("why_now"),
                "buying_signals": item.get("buying_signals")
                or ([item.get("why_now")] if item.get("why_now") else []),
                "published_at": item.get("content_occurred_at")
                or item.get("launch_date")
                or item.get("published_at")
                or item.get("last_verified"),
                "website_verified": True,
                "industry": "Technology",
                "description": item.get("why_now") or item.get("company"),
                "attributes": {
                    "source": item.get("source"),
                    "source_kind": "event",
                    "lead_eligible": True,
                },
            }
            lqs = scorer.score(payload)
            if not lqs.outbound_ready:
                continue
            ranked.append(
                {
                    **item,
                    "lead_quality_score": lqs.total,
                    "lead_quality_grade": lqs.grade,
                    "perfect_lead": lqs.perfect,
                    "outbound_ready": True,
                    "lqs_blockers": lqs.blockers,
                    "age_hours": lqs.age_hours,
                }
            )
        ranked.sort(
            key=lambda r: (bool(r.get("perfect_lead")), float(r.get("lead_quality_score") or 0)),
            reverse=True,
        )

        return {
            "items": ranked[:10],
            "count": len(ranked[:10]),
            "freshness_hours": FRESH_HOURS,
            "fresh_only": True,
            "quality_bar": {
                "scoring_version": SCORING_VERSION,
                "outbound_threshold": OUTBOUND_THRESHOLD,
                "perfect_threshold": PERFECT_THRESHOLD,
            },
        }

    async def submit_review(self, company_id: UUID, label: str) -> dict[str, Any]:
        try:
            FounderReviewLabel(label)
        except ValueError:
            return {"status": "invalid_label", "allowed": [x.value for x in FounderReviewLabel]}
        self.session.add(
            RrpFounderReview(
                id=uuid.uuid4(),
                company_id=company_id,
                label=label,
                payload={"recorded_at": datetime.now(UTC).isoformat()},
            )
        )
        await self.session.commit()
        return {"status": "recorded", "company_id": str(company_id), "label": label}

    async def perfect(self, *, crawl_dm: bool = True) -> dict[str, Any]:
        before = await self._live_kpis()
        companies = (
            await self.session.execute(
                select(Company).where(Company.deleted_at.is_(None), Company.primary_domain.is_not(None))
            )
        ).scalars().all()
        # Only perfect existing Sales Ready — never expand dataset
        targets = [c for c in companies if (c.attributes or {}).get("rdap_sales_ready")]
        perfected = []
        promoted = []
        blocked = []
        blocker_counts: Counter[str] = Counter()
        conf_dist: list[float] = []
        trust_dist: list[float] = []

        for company in targets:
            result = self.pipeline.perfect(
                {
                    "id": str(company.id),
                    "name": company.name,
                    "primary_domain": company.primary_domain,
                    "attributes": company.attributes or {},
                },
                crawl_dm=crawl_dm,
            )
            perfected.append(result)
            attrs = dict(company.attributes or {})
            payload = result.payload
            attrs["industry"] = payload.get("industry")
            attrs["country"] = payload.get("country")
            attrs["description"] = payload.get("description")
            attrs["rrp_why_now"] = payload.get("why_now")
            attrs["rrp_why_now_evidence"] = payload.get("why_now_evidence")
            attrs["rrp_confidence"] = payload.get("confidence")
            attrs["rrp_trust"] = payload.get("trust")
            attrs["rrp_revenue_ready"] = result.revenue_ready
            attrs["rdap_revenue_ready"] = result.revenue_ready
            attrs["rdap_sales_ready"] = True
            attrs["rrp_perfected_at"] = datetime.now(UTC).isoformat()
            if result.decision_maker:
                attrs["decision_maker"] = f"{result.decision_maker.full_name} ({result.decision_maker.job_title})"
                attrs["rrp_decision_maker"] = result.decision_maker.model_dump(mode="json")
            if result.opportunity:
                attrs["rrp_opportunity"] = result.opportunity.model_dump(mode="json")
                attrs["cir_best_service"] = result.opportunity.recommended_service
            if payload.get("business_email"):
                attrs["business_email"] = payload["business_email"]
                attrs["ofc_business_email"] = payload["business_email"]
            else:
                # Pipeline rejected outreach-safe email — drop personal case-study leftovers
                local = str(attrs.get("business_email") or "").split("@")[0].lower()
                if "." in local and not any(
                    local == p or local.startswith(p + "+")
                    for p in (
                        "info",
                        "hello",
                        "contact",
                        "sales",
                        "support",
                        "team",
                        "marketing",
                        "founder",
                        "ceo",
                        "help",
                        "care",
                    )
                ):
                    attrs.pop("business_email", None)
                    attrs.pop("ofc_business_email", None)
            if payload.get("decision_maker_email"):
                attrs["rrp_decision_maker_email"] = payload["decision_maker_email"]
            else:
                attrs.pop("rrp_decision_maker_email", None)
            attrs["rrp_contact_categories"] = [c.model_dump(mode="json") for c in result.contacts]
            attrs["rrp_blockers"] = [b.value for b in result.blockers]
            company.attributes = attrs
            flag_modified(company, "attributes")

            self.session.add(
                RrpCompanyProfile(
                    id=uuid.uuid4(),
                    company_id=company.id,
                    revenue_ready=result.revenue_ready,
                    sales_ready=True,
                    confidence=float(payload.get("confidence") or 0),
                    trust=float(payload.get("trust") or 0),
                    blockers=[b.value for b in result.blockers],
                    opportunity=result.opportunity.model_dump(mode="json") if result.opportunity else {},
                    decision_maker=result.decision_maker.model_dump(mode="json") if result.decision_maker else {},
                    contacts=[c.model_dump(mode="json") for c in result.contacts],
                    payload=payload,
                    scoring_version="rrp-v1",
                )
            )
            conf_dist.append(float(payload.get("confidence") or 0))
            trust_dist.append(float(payload.get("trust") or 0))
            card = {
                "company_id": str(company.id),
                "company": company.name,
                "logo": None,
                "website": f"https://{company.primary_domain}",
                "decision_maker": attrs.get("decision_maker"),
                "decision_maker_email": attrs.get("rrp_decision_maker_email"),
                "business_email": attrs.get("business_email"),
                "why_now": attrs.get("rrp_why_now"),
                "recommended_service": (attrs.get("rrp_opportunity") or {}).get("recommended_service"),
                "confidence": attrs.get("rrp_confidence"),
                "trust": attrs.get("rrp_trust"),
                "revenue_ready": result.revenue_ready,
                "last_verified": (attrs.get("rrp_decision_maker") or {}).get("last_verified"),
                "evidence_count": len((attrs.get("rrp_opportunity") or {}).get("evidence") or []),
                "blockers": [b.value for b in result.blockers],
            }
            if result.revenue_ready:
                promoted.append(card)
            else:
                for b in result.blockers:
                    blocker_counts[b.value] += 1
                blocked.append(card)

        await self.session.flush()
        after = await self._live_kpis()
        top_10 = sorted(promoted, key=lambda x: float(x.get("confidence") or 0), reverse=True)[:10]
        answer = "YES" if after["revenue_ready"] >= 10 else "NO"
        audit = {
            "before": before,
            "after": after,
            "promoted": promoted,
            "still_blocked": blocked,
            "blocker_counts": dict(blocker_counts),
            "confidence_distribution": conf_dist,
            "trust_distribution": trust_dist,
            "top_10": top_10,
            "vansh_ready_answer": answer,
            "scoring_version": "rrp-v1",
            "impact_statement": (
                f"This change increased Revenue Ready companies from {before['revenue_ready']} to {after['revenue_ready']}."
            ),
        }
        self.session.add(
            RrpDailyReport(
                id=uuid.uuid4(),
                payload=audit,
                revenue_ready=after["revenue_ready"],
                sales_ready=after["sales_ready"],
                vansh_ready_answer=answer,
                scoring_version="rrp-v1",
            )
        )
        await self.session.commit()
        return audit
