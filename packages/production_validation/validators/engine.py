from __future__ import annotations

from uuid import UUID

from production_validation.models.types import (
    READINESS_GATE,
    LeadReadinessChecklist,
    LeadReadinessResult,
    ProductionValidationInput,
)


class LeadQualityValidator:
    """Production readiness score — companies below gate never enter outreach."""

    WEIGHTS = {
        "website": 8.0,
        "business_email": 10.0,
        "decision_maker": 12.0,
        "linkedin": 6.0,
        "technology": 6.0,
        "industry": 6.0,
        "buying_trigger": 8.0,
        "pain_point": 8.0,
        "revenue_estimate": 6.0,
        "service_match": 10.0,
        "confidence": 8.0,
        "freshness": 6.0,
        "verification": 6.0,
    }

    def score(self, item: ProductionValidationInput) -> LeadReadinessResult:
        if item.company_id is None:
            raise ValueError("company_id required for lead readiness")
        checklist = LeadReadinessChecklist(
            website=bool(item.website),
            business_email=bool(item.business_email and "@" in item.business_email),
            decision_maker=bool(item.decision_makers),
            linkedin=bool(item.linkedin_url),
            technology=bool(item.technologies),
            industry=bool(item.industry),
            buying_trigger=bool(item.buying_triggers),
            pain_point=bool(item.pain_points),
            revenue_estimate=bool(item.revenue_estimate),
            service_match=bool(item.service_match),
            confidence=item.confidence >= 70.0,
            freshness=item.freshness_days <= 30,
            verification=item.verification_score >= 70.0,
        )
        score = 0.0
        evidence: list[str] = []
        blocking: list[str] = []
        for key, weight in self.WEIGHTS.items():
            ok = bool(getattr(checklist, key))
            if ok:
                score += weight
                evidence.append(f"{key}:pass")
            else:
                blocking.append(key)
                evidence.append(f"{key}:fail")
        score = round(min(100.0, score), 4)
        allowed = score >= READINESS_GATE
        if not allowed:
            evidence.append(f"gate:{READINESS_GATE}")
            evidence.append("outreach_blocked:true")
        return LeadReadinessResult(
            company_id=item.company_id,
            company_name=item.company_name,
            score=score,
            checklist=checklist,
            outreach_allowed=allowed,
            evidence=evidence,
            blocking_reasons=blocking,
        )


class CampaignFunnelValidator:
    def snapshots(self, item: ProductionValidationInput) -> list:
        from production_validation.models.types import CampaignFunnelSnapshot

        out = []
        campaigns = item.campaigns or [item.funnel]
        for raw in campaigns:
            if not raw:
                continue
            cid = raw.get("campaign_id")
            company_id = raw.get("company_id") or item.company_id
            out.append(
                CampaignFunnelSnapshot(
                    campaign_id=UUID(str(cid)) if cid else None,
                    company_id=UUID(str(company_id)) if company_id else item.company_id,
                    company_name=str(raw.get("company_name") or item.company_name),
                    emails_sent=int(raw.get("emails_sent") or raw.get("emails") or 0),
                    delivered=int(raw.get("delivered") or 0),
                    opened=int(raw.get("opened") or 0),
                    clicked=int(raw.get("clicked") or 0),
                    replies=int(raw.get("replies") or 0),
                    meetings=int(raw.get("meetings") or 0),
                    proposals=int(raw.get("proposals") or 0),
                    won=int(raw.get("won") or 0),
                    revenue=float(raw.get("revenue") or 0.0),
                    stage=str(raw.get("stage") or "unknown"),
                    evidence=[f"stage:{raw.get('stage') or 'unknown'}"],
                )
            )
        return out
