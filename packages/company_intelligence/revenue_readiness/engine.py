"""Revenue Readiness — explainable weighted score → classification."""

from __future__ import annotations

from typing import Any

from company_intelligence.models.types import (
    UNKNOWN,
    BuyingSignal,
    CirClassification,
    CompanyBusinessProfile,
    ContactPerson,
    IcpProfile,
    RevenueReadinessScore,
    ServiceMatch,
    TechnologyHit,
    WebsiteCorpus,
)

# Scored dimensions sum to 100. Evidence density is reported as Trust (not double-counted).
WEIGHTS = {
    "identity": 15.0,
    "website": 10.0,
    "business": 15.0,
    "technology": 10.0,
    "icp": 10.0,
    "buying_intent": 15.0,
    "service_match": 15.0,
    "contacts": 10.0,
}


class RevenueReadinessEngine:
    def score(
        self,
        *,
        erowd_admitted: bool,
        corpus: WebsiteCorpus,
        business: CompanyBusinessProfile,
        icp: IcpProfile,
        technologies: list[TechnologyHit],
        signals: list[BuyingSignal],
        matches: list[ServiceMatch],
        contacts: list[ContactPerson],
        payload: dict[str, Any] | None = None,
    ) -> RevenueReadinessScore:
        payload = payload or {}
        evidence: list[str] = []

        identity = WEIGHTS["identity"] if erowd_admitted or payload.get("erowd_verified") else 0.0
        if identity:
            evidence.append("identity:erowd_admitted:+15")

        website = 0.0
        if corpus.crawled and corpus.page_count >= 1:
            website = min(WEIGHTS["website"], 4.0 + corpus.page_count * 1.5)
            evidence.append(f"website_pages:{corpus.page_count}:+{website:.1f}")
        elif corpus.website and corpus.website != UNKNOWN:
            website = 4.0
            evidence.append("website_url_only:+4")

        business_pts = 0.0
        filled = sum(
            1
            for f in (
                business.description,
                business.industry,
                business.primary_product,
                business.business_model,
                business.country,
            )
            if f.value != UNKNOWN
        )
        business_pts = min(WEIGHTS["business"], filled * 3.0)
        if business_pts:
            evidence.append(f"business_fields:{filled}:+{business_pts:.1f}")

        tech_pts = min(WEIGHTS["technology"], len(technologies) * 2.5)
        if tech_pts:
            evidence.append(f"technologies:{len(technologies)}:+{tech_pts:.1f}")

        icp_pts = 0.0
        if icp.primary_icp.value != UNKNOWN:
            icp_pts = min(WEIGHTS["icp"], 6.0 + icp.confidence / 25.0)
            evidence.append(f"icp:{icp.primary_icp.value}:+{icp_pts:.1f}")

        intent_pts = min(WEIGHTS["buying_intent"], len(signals) * 4.0)
        if intent_pts:
            evidence.append(f"buying_signals:{len(signals)}:+{intent_pts:.1f}")

        match_pts = 0.0
        if matches:
            match_pts = min(WEIGHTS["service_match"], matches[0].need_score / 100.0 * WEIGHTS["service_match"])
            evidence.append(f"service_match:{matches[0].service}:+{match_pts:.1f}")

        named = [c for c in contacts if c.name != UNKNOWN]
        emailed = [c for c in contacts if c.email != UNKNOWN]
        contact_pts = min(WEIGHTS["contacts"], len(named) * 3.0 + len(emailed) * 4.0)
        if contact_pts:
            evidence.append(f"contacts_named:{len(named)}_email:{len(emailed)}:+{contact_pts:.1f}")

        evidence_pts = min(
            10.0,
            (
                (3.0 if business.description.value != UNKNOWN else 0.0)
                + (2.0 if technologies else 0.0)
                + (2.0 if signals else 0.0)
                + (2.0 if matches else 0.0)
                + (1.0 if contacts else 0.0)
            ),
        )
        if evidence_pts:
            evidence.append(f"evidence_density:{evidence_pts:.1f}")

        total = round(
            identity + website + business_pts + tech_pts + icp_pts + intent_pts + match_pts + contact_pts,
            2,
        )
        # Trust is derived from evidence density (0-100), not a separate additive weight
        trust = round(min(100.0, evidence_pts * 10), 2)
        classification = self._classify(total)
        return RevenueReadinessScore(
            total=total,
            identity=round(identity, 2),
            website=round(website, 2),
            business=round(business_pts, 2),
            technology=round(tech_pts, 2),
            icp=round(icp_pts, 2),
            buying_intent=round(intent_pts, 2),
            service_match=round(match_pts, 2),
            contacts=round(contact_pts, 2),
            evidence_score=round(evidence_pts, 2),
            trust=trust,
            classification=classification,
            breakdown=dict(WEIGHTS),
            evidence=evidence + [f"total:{total}", f"class:{classification.value}"],
        )

    def _classify(self, total: float) -> CirClassification:
        if total >= 90:
            return CirClassification.PRIORITY_ACCOUNT
        if total >= 75:
            return CirClassification.REVENUE_READY
        if total >= 60:
            return CirClassification.PROMISING
        if total >= 40:
            return CirClassification.OBSERVED
        return CirClassification.REJECTED
