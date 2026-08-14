from __future__ import annotations

from datetime import UTC, datetime

from account_intelligence.business_profile.engine import (
    AIReadinessEngine,
    BusinessProfileEngine,
    FinancialProfileEngine,
    GrowthAnalysisEngine,
    IndustryBenchmarkEngine,
    SalesReadinessEngine,
)
from account_intelligence.buying_committee.engine import BuyingCommitteeEngine, ContactDiscoveryEngine, ContactValidationEngine
from account_intelligence.company_profile.engine import CompanyProfileEngine, ConfidenceEngine
from account_intelligence.models.types import (
    SCORING_VERSION,
    LICENSED_PROVIDERS_DISABLED,
    AccountIntelligenceDecision,
    AccountIntelligenceInput,
)
from account_intelligence.relationship_graph.engine import (
    CompanyStructureEngine,
    RelationshipGraphEngine,
    TimelineEngine,
    VerificationEngine,
)
from account_intelligence.technology_enrichment.engine import (
    AIStackEngine,
    CloudStackEngine,
    CRMDetectionEngine,
    MarketingStackEngine,
    SecurityStackEngine,
    TechnologyEnrichmentEngine,
    WebsiteEnrichmentEngine,
)


class AccountIntelligencePipeline:
    """Compose-only Master Enrichment Platform — GOAP opportunities → sales-ready accounts."""

    def __init__(self) -> None:
        self.profile = CompanyProfileEngine()
        self.confidence = ConfidenceEngine()
        self.discovery = ContactDiscoveryEngine()
        self.committee = BuyingCommitteeEngine()
        self.validation = ContactValidationEngine()
        self.tech = TechnologyEnrichmentEngine()
        self.website = WebsiteEnrichmentEngine()
        self.crm = CRMDetectionEngine()
        self.marketing = MarketingStackEngine()
        self.security = SecurityStackEngine()
        self.cloud = CloudStackEngine()
        self.ai_stack = AIStackEngine()
        self.financial = FinancialProfileEngine()
        self.growth = GrowthAnalysisEngine()
        self.business = BusinessProfileEngine()
        self.ai_ready = AIReadinessEngine()
        self.sales_ready = SalesReadinessEngine()
        self.structure = CompanyStructureEngine()
        self.graph = RelationshipGraphEngine()
        self.verification = VerificationEngine()
        self.timeline = TimelineEngine()
        self.benchmarks = IndustryBenchmarkEngine()

    def process(self, item: AccountIntelligenceInput) -> AccountIntelligenceDecision:
        now = item.now or datetime.now(UTC)
        profile = self.profile.build(item)
        observed = self.discovery.discover(item)
        committee = self.committee.discover(item)
        verified = self.validation.validate(observed, domain=item.domain, now=now)
        tech = self.tech.enrich(item)
        # compose stack detectors (no redesign — they project from tech)
        _ = self.crm.detect(tech), self.marketing.detect(tech), self.security.detect(tech), self.cloud.detect(tech), self.ai_stack.detect(tech)
        website = self.website.enrich(item)
        financial = self.financial.build(item)
        growth = self.growth.build(item)
        business = self.business.build(item, tech=tech, website=website)
        ai = self.ai_ready.score(item, tech=tech, website=website, business=business)
        sales = self.sales_ready.score(
            item,
            committee_count=len(committee),
            verified_count=sum(1 for v in verified if v.accepted),
            tech=tech,
            business=business,
            ai=ai,
            profile_confidence=profile.overall_confidence,
        )
        departments = self.structure.departments(committee)
        graph = self.graph.build(item, committee=committee, verified=verified, tech=tech, departments=departments)
        conf = self.confidence.report(
            profile,
            extras={
                "technology": tech.confidence,
                "website": website.confidence,
                "business": business.confidence,
                "sales_readiness": sales.score,
                "ai_readiness": ai.overall,
            },
        )
        profile_fields = {
            "company_name": (profile.company_name.confidence, profile.company_name.source),
            "website": (profile.website.confidence, profile.website.source),
            "industry": (profile.industry.confidence, profile.industry.source),
            "employee_count": (profile.employee_count.confidence, profile.employee_count.source),
            "revenue_estimate": (profile.revenue_estimate.confidence, profile.revenue_estimate.source),
        }
        vhist = self.verification.history(profile_fields=profile_fields, verified_contacts=verified, now=now)
        timeline = self.timeline.build(
            item,
            events=[f"sales_readiness:{sales.category.value}", f"ai_readiness:{ai.overall}"],
        )
        evidence = [
            f"scoring_version:{SCORING_VERSION}",
            "compose_only:true",
            "no_gpt:true",
            "never_fabricate:true",
            f"committee:{len(committee)}",
            f"verified:{sum(1 for v in verified if v.accepted)}",
            f"sales:{sales.category.value}",
            f"licensed_disabled:{','.join(LICENSED_PROVIDERS_DISABLED)}",
        ]
        return AccountIntelligenceDecision(
            company_id=item.company_id,
            company_name=item.company_name,
            profile=profile,
            departments=departments,
            locations=list(profile.locations),
            buying_committee=committee,
            verified_contacts=verified,
            technology=tech,
            website=website,
            financial=financial,
            business=business,
            growth=growth,
            ai_readiness=ai,
            sales_readiness=sales,
            relationship_graph=graph,
            confidence=conf,
            verification_history=vhist,
            timeline=timeline,
            industry_benchmark=self.benchmarks.for_industry(item.industry),
            licensed_providers_disabled=list(LICENSED_PROVIDERS_DISABLED),
            scoring_version=SCORING_VERSION,
            evidence_chain=evidence,
            evaluated_at=now,
        )
