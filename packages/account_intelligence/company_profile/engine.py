from __future__ import annotations

from datetime import UTC, datetime

from account_intelligence.confidence_engine.fields import field
from account_intelligence.models.types import (
    AccountIntelligenceInput,
    CompanyLocation,
    ConfidenceReport,
    FieldValue,
    MasterAccountProfile,
)


class CompanyProfileEngine:
    def build(self, item: AccountIntelligenceInput) -> MasterAccountProfile:
        now = item.now or datetime.now(UTC)
        src = item.source_attribution or "goap"

        def f(name: str, value, conf: float = 70.0) -> FieldValue:
            source = item.field_sources.get(name, src)
            return field(value, confidence=conf if value is not None else 0.0, source=source, now=now, evidence=[f"field:{name}"])

        locations = [
            CompanyLocation(
                label=str(loc.get("label") or loc.get("city") or "Office"),
                country=loc.get("country"),
                state=loc.get("state"),
                city=loc.get("city"),
                is_hq=bool(loc.get("is_hq")),
                confidence=float(loc.get("confidence") or 60.0),
                source=str(loc.get("source") or src),
                last_verified=now,
                evidence=[f"location:{loc.get('label') or loc.get('city')}"],
            )
            for loc in item.locations
            if isinstance(loc, dict)
        ]
        if item.city or item.country:
            locations.insert(
                0,
                CompanyLocation(
                    label="HQ" if item.city else (item.country or "HQ"),
                    country=item.country,
                    state=item.state,
                    city=item.city,
                    is_hq=True,
                    confidence=75.0 if item.city else 55.0,
                    source=src,
                    last_verified=now,
                    evidence=["hq:inferred_from_profile"],
                ),
            )

        fields = {
            "company_name": f("company_name", item.company_name, 95.0),
            "website": f("website", item.website or (f"https://{item.domain}" if item.domain else None), 80.0 if item.website or item.domain else 0.0),
            "legal_name": f("legal_name", item.legal_name, 70.0),
            "industry": f("industry", item.industry, 75.0),
            "sub_industry": f("sub_industry", item.sub_industry, 65.0),
            "business_model": f("business_model", item.business_model, 60.0),
            "country": f("country", item.country, 70.0),
            "state": f("state", item.state, 60.0),
            "city": f("city", item.city, 60.0),
            "founded": f("founded", item.founded, 55.0),
            "employee_count": f("employee_count", item.employee_count, 50.0),
            "revenue_estimate": f("revenue_estimate", item.revenue_estimate, 40.0),
            "funding": f("funding", item.funding, 55.0),
            "latest_funding_round": f("latest_funding_round", item.latest_funding_round, 55.0),
            "investors": f("investors", item.investors or None, 50.0),
            "offices": f("offices", item.offices or None, 50.0),
            "time_zone": f("time_zone", item.time_zone, 45.0),
            "languages": f("languages", item.languages or None, 45.0),
            "parent_company": f("parent_company", item.parent_company, 50.0),
            "subsidiaries": f("subsidiaries", item.subsidiaries or None, 50.0),
            "public_company_status": f("public_company_status", ("public" if item.is_public else ("private" if item.is_public is False else None)), 60.0),
            "ipo_status": f("ipo_status", item.ipo_status, 50.0),
            "annual_growth": f("annual_growth", item.annual_growth, 45.0),
            "hiring_trend": f("hiring_trend", item.hiring_trend, 45.0),
            "expansion_score": f("expansion_score", item.expansion_score, 45.0),
        }
        confidences = [v.confidence for v in fields.values() if v.value is not None]
        overall = round(sum(confidences) / len(confidences), 2) if confidences else 0.0
        return MasterAccountProfile(
            **fields,
            locations=locations,
            overall_confidence=overall,
            source=src,
            last_verified=now,
            evidence=[f"fields_present:{len(confidences)}", "never_fabricate:true"],
        )


class ConfidenceEngine:
    def report(self, profile: MasterAccountProfile, extras: dict[str, float] | None = None) -> ConfidenceReport:
        field_scores: dict[str, float] = {}
        sources: dict[str, str] = {}
        conflicts: list[str] = []
        for name in [
            "company_name",
            "website",
            "industry",
            "country",
            "employee_count",
            "revenue_estimate",
            "funding",
            "hiring_trend",
        ]:
            fv: FieldValue = getattr(profile, name)
            field_scores[name] = fv.confidence
            sources[name] = fv.source
            conflicts.extend(fv.conflicts)
        if extras:
            field_scores.update(extras)
        present = [v for v in field_scores.values() if v > 0]
        overall = round(sum(present) / len(present), 2) if present else 0.0
        return ConfidenceReport(
            field_scores=field_scores,
            overall=overall,
            conflicts=conflicts,
            sources=sources,
            evidence=[f"overall:{overall}", "history:append_only"],
        )
