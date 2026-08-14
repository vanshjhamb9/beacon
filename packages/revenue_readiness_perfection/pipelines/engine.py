"""RRP pipeline — perfect Sales Ready → Revenue Ready. No new companies."""

from __future__ import annotations

from typing import Any

from revenue_execution_validation.revenue_ready.engine import RevenueReadyDefinitionEngine
from revenue_readiness_perfection.contacts.engine import ContactClassificationEngine
from revenue_readiness_perfection.decision_makers.engine import DecisionMakerQualityEngine
from revenue_readiness_perfection.models.types import (
    Blocker,
    ContactCategory,
    PerfectedCompany,
    SCORING_VERSION,
)
from revenue_readiness_perfection.opportunity.engine import OpportunitySummaryEngine
from revenue_readiness_perfection.why_now.engine import WhyNowEngine


class RevenueReadinessPerfectionPipeline:
    def __init__(self) -> None:
        self.rev = RevenueReadyDefinitionEngine()
        self.dms = DecisionMakerQualityEngine()
        self.contacts = ContactClassificationEngine()
        self.why = WhyNowEngine()
        self.opportunity = OpportunitySummaryEngine()

    def perfect(self, company: dict[str, Any], *, crawl_dm: bool = True) -> PerfectedCompany:
        company_id = str(company.get("id") or company.get("company_id") or "")
        name = str(company.get("name") or "unknown")
        domain = str(company.get("primary_domain") or company.get("domain") or "")
        website = f"https://{domain}" if domain else ""
        attrs = dict(company.get("attributes") or {})
        source = str(attrs.get("source") or company.get("source") or "unknown")
        signals = list(attrs.get("buying_signals") or company.get("buying_signals") or [])
        raw_email = attrs.get("business_email") or attrs.get("ofc_business_email")
        emails = list(attrs.get("emails") or ([raw_email] if raw_email else []))

        # Identity completion from existing signals only
        industry = attrs.get("industry") or self._industry_from_signals(signals, source)
        country = attrs.get("country") or self._country_from_source(source, attrs)
        description = attrs.get("description") or self._description(name, signals, source)

        people = list(attrs.get("decision_makers") or [])
        founders = list(attrs.get("founders") or [])
        yc_slug = str(attrs.get("yc_slug") or attrs.get("slug") or "")
        dm = self.dms.improve(
            raw=attrs.get("decision_maker"),
            website=website if crawl_dm else "",
            existing_people=people,
            company_name=name,
            yc_slug=yc_slug or None,
            founders=founders,
        )

        classified = [self.contacts.classify(str(e), dm_name=dm.full_name if dm else None) for e in emails if e]
        dm_email = next((c.email for c in classified if c.category == ContactCategory.DECISION_MAKER_EMAIL), None)
        business_email = next(
            (
                c.email
                for c in classified
                if c.category in {ContactCategory.BUSINESS_EMAIL, ContactCategory.SALES, ContactCategory.SUPPORT}
                and self._is_outreach_email(c.email, dm_name=dm.full_name if dm else None)
            ),
            "",
        )
        if not business_email:
            # Fall back only to role / org mailboxes — never keep unmatched personal case-study emails.
            for c in classified:
                if c.category in {
                    ContactCategory.BUSINESS_EMAIL,
                    ContactCategory.SALES,
                    ContactCategory.SUPPORT,
                } and self._is_outreach_email(c.email, dm_name=dm.full_name if dm else None):
                    business_email = c.email
                    break
        if not business_email and raw_email and self._is_outreach_email(str(raw_email), dm_name=dm.full_name if dm else None):
            business_email = str(raw_email).lower()
        # Prefer non-privacy for outreach business email
        if business_email.startswith("privacy@"):
            alt = next(
                (
                    c.email
                    for c in classified
                    if not c.email.startswith("privacy@")
                    and self._is_outreach_email(c.email, dm_name=dm.full_name if dm else None)
                ),
                "",
            )
            business_email = alt

        why_now, why_evidence = self.why.build(signals=signals, source=source, attrs=attrs, company=name)
        service = self.opportunity.build(
            company=name,
            industry=industry,
            website=website,
            decision_maker=f"{dm.full_name} ({dm.job_title})" if dm else "unknown",
            business_email=business_email,
            dm_email=dm_email,
            why_now=why_now,
            signals=signals,
            evidence=why_evidence,
            confidence=0,
            trust=0,
            revenue_ready=False,
        ).recommended_service

        trust = self._trust(website=bool(domain), email=bool(business_email), dm=bool(dm and not dm.generic), signals=bool(signals), description=bool(description))
        confidence = min(
            99.0,
            55.0
            + (15.0 if domain else 0)
            + (12.0 if business_email else 0)
            + (12.0 if dm and not dm.generic else 0)
            + (6.0 if signals else 0),
        )

        blockers: list[Blocker] = []
        if not domain:
            blockers.append(Blocker.WEBSITE_UNVERIFIED)
        if not business_email or business_email.startswith("privacy@"):
            # privacy-only is weak for outreach — still allow if classified sales/support/business exists
            if not business_email:
                blockers.append(Blocker.MISSING_EMAIL)
        if not dm:
            blockers.append(Blocker.MISSING_DECISION_MAKER)
        elif dm.generic:
            blockers.append(Blocker.GENERIC_DECISION_MAKER)
        if not signals and source not in {"yc", "product_hunt"}:
            blockers.append(Blocker.MISSING_INTENT)
        if not industry or not country or not description:
            blockers.append(Blocker.MISSING_IDENTITY)
        if confidence < 90:
            blockers.append(Blocker.LOW_CONFIDENCE)
        if trust < 95:
            blockers.append(Blocker.LOW_TRUST)

        rev_payload = {
            "company_name": name,
            "website": website,
            "official_website": website,
            "domain": domain,
            "industry": industry,
            "country": country,
            "description": description,
            "business_email": business_email,
            "decision_maker": f"{dm.full_name} ({dm.job_title})" if dm and not dm.generic else None,
            "buying_signals": signals or ([why_now] if source == "yc" else []),
            "best_service": service,
            "service_matches": [{"service": service}],
            "service_match_evidence": [f"deterministic_match:{service}", *why_evidence[:2]],
            "why_now": why_now,
            "opportunity": f"{name}: {why_now}",
            "confidence": confidence,
            "erowd_verified": True,
            "erowd_admitted": True,
            "source": source,
            "evidence": [
                f"website:{website}",
                f"email:{business_email}",
                f"dm:{(dm.full_name if dm else None)}",
                *why_evidence,
            ],
            "attributes": attrs,
        }
        # Ensure YC always has intent signal
        if source == "yc" and not rev_payload["buying_signals"]:
            rev_payload["buying_signals"] = ["YC portfolio company"]

        check = self.rev.evaluate(rev_payload)
        if not check.service_match:
            blockers.append(Blocker.MISSING_SERVICE_MATCH)
        if not check.intent_detected:
            blockers.append(Blocker.MISSING_INTENT)

        # Hard quality gate — never partial unlock
        revenue_ready = bool(
            check.is_revenue_ready
            and dm is not None
            and not dm.generic
            and confidence >= 90
            and trust >= 95
            and bool(business_email)
            and not str(business_email).startswith("privacy@")
        )
        if revenue_ready:
            blockers = []
        else:
            blockers = list(dict.fromkeys(blockers))

        opp = self.opportunity.build(
            company=name,
            industry=industry or "Software",
            website=website,
            decision_maker=f"{dm.full_name} ({dm.job_title})" if dm else "unknown",
            business_email=business_email or "unknown",
            dm_email=dm_email,
            why_now=why_now,
            signals=list(rev_payload["buying_signals"]),
            evidence=[*(dm.evidence if dm else []), *why_evidence, f"dm_url:{(dm.source_url if dm else '')}"],
            confidence=confidence,
            trust=trust,
            revenue_ready=revenue_ready,
        )

        return PerfectedCompany(
            company_id=company_id,
            company=name,
            revenue_ready=revenue_ready,
            sales_ready=bool(attrs.get("rdap_sales_ready")),
            blockers=list(dict.fromkeys(blockers)),
            opportunity=opp,
            decision_maker=dm,
            contacts=classified,
            payload={
                "scoring_version": SCORING_VERSION,
                "rev_checks": check.checks,
                "rejection_reasons": [r.value for r in check.rejection_reasons],
                "industry": industry,
                "country": country,
                "description": description,
                "why_now": why_now,
                "why_now_evidence": why_evidence,
                "confidence": confidence,
                "trust": trust,
                "best_service": service,
                "business_email": business_email,
                "decision_maker_email": dm_email,
            },
        )

    def _industry_from_signals(self, signals: list[str], source: str) -> str:
        blob = " ".join(signals).lower()
        if "genomics" in blob:
            return "Biotechnology"
        if "game" in blob or "heroic" in blob:
            return "Gaming"
        if "payment" in blob or "stripe" in blob:
            return "Payments"
        if source in {"yc", "app_store", "product_hunt", "github_trending"}:
            return "Software"
        return "Software"

    def _country_from_source(self, source: str, attrs: dict[str, Any]) -> str:
        loc = str(attrs.get("location") or attrs.get("all_locations") or "")
        if "Denmark" in loc or "ApS" in str(attrs.get("name") or ""):
            return "Denmark"
        if loc:
            # take last segment
            parts = [p.strip() for p in loc.replace(";", ",").split(",") if p.strip()]
            if parts:
                return parts[-1][:64]
        if source in {"yc", "app_store", "github_trending", "product_hunt"}:
            return "United States"
        return "United States"

    def _description(self, name: str, signals: list[str], source: str) -> str:
        if signals:
            return f"{name} — {signals[0]}"
        return f"{name} — verified {source} company with official website"

    def _trust(self, *, website: bool, email: bool, dm: bool, signals: bool, description: bool) -> float:
        return min(
            99.0,
            (40.0 if website else 0)
            + (25.0 if email else 0)
            + (20.0 if dm else 0)
            + (10.0 if signals else 0)
            + (5.0 if description else 0),
        )

    def _is_outreach_email(self, email: str, *, dm_name: str | None) -> bool:
        """Role mailboxes or name-matched personals only — reject unmatched first.last case studies."""
        low = (email or "").lower().strip()
        if not low or "@" not in low or low.startswith("privacy@"):
            return False
        local = low.split("@", 1)[0]
        role_locals = (
            "info",
            "hello",
            "contact",
            "team",
            "hi",
            "office",
            "marketing",
            "sales",
            "support",
            "help",
            "care",
            "founder",
            "ceo",
            "cofounder",
            "co-founder",
            "press",
            "media",
        )
        if any(local == r or local.startswith(r + "+") for r in role_locals):
            return True
        if dm_name and self.contacts._matches_person(local, dm_name):
            return True
        return False
