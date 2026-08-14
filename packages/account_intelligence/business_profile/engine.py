from __future__ import annotations

from datetime import UTC, datetime

from account_intelligence.confidence_engine.fields import field
from account_intelligence.models.types import (
    AccountIntelligenceInput,
    AIReadinessReport,
    BusinessProfile,
    FinancialProfile,
    GrowthProfile,
    IndustryBenchmark,
    SalesReadinessCategory,
    SalesReadinessReport,
    TechnologyProfile,
    WebsiteEnrichment,
)


class FinancialProfileEngine:
    def build(self, item: AccountIntelligenceInput) -> FinancialProfile:
        now = item.now or datetime.now(UTC)
        src = item.source_attribution
        return FinancialProfile(
            revenue_estimate=field(item.revenue_estimate, confidence=40.0 if item.revenue_estimate is not None else 0.0, source=src, now=now),
            funding=field(item.funding, confidence=55.0 if item.funding else 0.0, source=src, now=now),
            latest_funding_round=field(item.latest_funding_round, confidence=55.0 if item.latest_funding_round else 0.0, source=src, now=now),
            investors=field(item.investors or None, confidence=50.0 if item.investors else 0.0, source=src, now=now),
            evidence=["never_fabricate_finance:true"],
        )


class GrowthAnalysisEngine:
    def build(self, item: AccountIntelligenceInput) -> GrowthProfile:
        now = item.now or datetime.now(UTC)
        src = item.source_attribution
        return GrowthProfile(
            annual_growth=field(item.annual_growth, confidence=45.0 if item.annual_growth is not None else 0.0, source=src, now=now),
            hiring_trend=field(item.hiring_trend, confidence=45.0 if item.hiring_trend is not None else 0.0, source=src, now=now),
            expansion_score=field(item.expansion_score, confidence=45.0 if item.expansion_score is not None else 0.0, source=src, now=now),
            evidence=["growth:observed_only"],
        )


class BusinessProfileEngine:
    def build(
        self,
        item: AccountIntelligenceInput,
        *,
        tech: TechnologyProfile,
        website: WebsiteEnrichment,
    ) -> BusinessProfile:
        now = item.now or datetime.now(UTC)
        employees = item.employee_count or 0
        if employees >= 500 or item.latest_funding_round in {"series_c", "ipo"}:
            stage = "scale"
        elif employees >= 50 or item.latest_funding_round in {"series_a", "series_b"}:
            stage = "growth"
        elif employees >= 10 or item.funding:
            stage = "early"
        else:
            stage = "startup"
        digital = min(100.0, website.seo_score * 0.3 + website.performance_score * 0.3 + (20.0 if website.ssl else 0) + (10.0 if website.mobile else 0))
        automation = min(100.0, 20.0 + len(tech.marketing_automation) * 15 + len(tech.crm) * 15 + (15.0 if website.automation else 0))
        ai_adopt = min(100.0, 15.0 + len(tech.ai_stack) * 20 + len(tech.llm_stack) * 15 + (10.0 if website.ai_widgets else 0))
        software = min(100.0, 25.0 + len(tech.frontend + tech.backend + tech.cloud) * 8)
        risks = []
        if not website.ssl:
            risks.append("missing_ssl")
        if not tech.crm:
            risks.append("no_crm_detected")
        if digital < 40:
            risks.append("low_digital_maturity")
        opportunities = []
        if not website.chatbot:
            opportunities.append("chatbot")
        if not tech.crm:
            opportunities.append("crm")
        if ai_adopt < 40:
            opportunities.append("ai_automation")
        segment = "enterprise" if employees >= 500 else ("midmarket" if employees >= 50 else "smb")
        return BusinessProfile(
            growth_stage=stage,
            digital_maturity=round(digital, 2),
            automation_level=round(automation, 2),
            ai_adoption=round(ai_adopt, 2),
            software_maturity=round(software, 2),
            customer_segment=segment,
            market_position="challenger" if stage in {"growth", "scale"} else "emerging",
            competitive_position="unknown",
            buying_intent=max(0.0, min(100.0, float(item.buying_intent))),
            business_risks=risks,
            growth_opportunities=opportunities,
            confidence=round(min(90.0, 40.0 + (10.0 if item.industry else 0) + (10.0 if employees else 0)), 2),
            source="inferred",
            last_verified=now,
            evidence=[f"stage:{stage}", f"segment:{segment}"],
        )


class AIReadinessEngine:
    def score(
        self,
        item: AccountIntelligenceInput,
        *,
        tech: TechnologyProfile,
        website: WebsiteEnrichment,
        business: BusinessProfile,
    ) -> AIReadinessReport:
        now = item.now or datetime.now(UTC)
        need_ai = min(100.0, 40.0 + (30.0 if business.ai_adoption < 40 else 10.0) + (20.0 if not tech.ai_stack else 0))
        need_crm = 80.0 if not tech.crm else 25.0
        need_erp = 70.0 if not tech.erp and (item.employee_count or 0) >= 100 else 20.0
        need_saas = min(100.0, 35.0 + business.software_maturity * 0.3)
        need_website = 75.0 if website.performance_score < 50 or not website.mobile else 25.0
        need_mobile = 65.0 if "mobile app" in " ".join(item.html_hints).lower() or not website.mobile else 20.0
        need_custom = min(100.0, 30.0 + len(business.growth_opportunities) * 12)
        need_chatbot = 80.0 if not website.chatbot else 20.0
        need_internal = min(100.0, 35.0 + (item.hiring_trend or 0) * 0.3)
        need_analytics = 70.0 if not tech.analytics else 25.0
        need_kb = 65.0 if not website.knowledge_base else 20.0
        need_workflow = 75.0 if business.automation_level < 40 else 30.0
        need_integrations = min(100.0, 40.0 + len(tech.crm + tech.erp) * 10)
        scores = [
            need_ai,
            need_crm,
            need_erp,
            need_saas,
            need_website,
            need_mobile,
            need_custom,
            need_chatbot,
            need_internal,
            need_analytics,
            need_kb,
            need_workflow,
            need_integrations,
        ]
        overall = round(sum(scores) / len(scores), 2)
        return AIReadinessReport(
            need_ai_automation=round(need_ai, 2),
            need_crm=round(need_crm, 2),
            need_erp=round(need_erp, 2),
            need_saas=round(need_saas, 2),
            need_website=round(need_website, 2),
            need_mobile_app=round(need_mobile, 2),
            need_custom_software=round(need_custom, 2),
            need_chatbot=round(need_chatbot, 2),
            need_internal_ai=round(need_internal, 2),
            need_analytics=round(need_analytics, 2),
            need_knowledge_base=round(need_kb, 2),
            need_workflow_automation=round(need_workflow, 2),
            need_integrations=round(need_integrations, 2),
            overall=overall,
            confidence=75.0,
            source="aip",
            last_verified=now,
            evidence=[f"overall:{overall}"],
        )


class SalesReadinessEngine:
    def score(
        self,
        item: AccountIntelligenceInput,
        *,
        committee_count: int,
        verified_count: int,
        tech: TechnologyProfile,
        business: BusinessProfile,
        ai: AIReadinessReport,
        profile_confidence: float,
    ) -> SalesReadinessReport:
        now = item.now or datetime.now(UTC)
        opportunity = min(100.0, business.buying_intent)
        budget = min(100.0, (40.0 if item.funding or item.revenue_estimate else 15.0) + (20.0 if item.latest_funding_round else 0))
        authority = min(100.0, committee_count * 25.0)
        need = min(100.0, ai.overall)
        timing = min(100.0, 30.0 + (item.hiring_trend or 0) * 0.4 + (item.expansion_score or 0) * 0.3)
        completeness = min(100.0, profile_confidence)
        decision_makers = min(100.0, committee_count * 30.0)
        contact_avail = min(100.0, verified_count * 35.0)
        technology = min(100.0, tech.confidence)
        growth = min(100.0, (item.annual_growth or 0) + (item.hiring_trend or 0) * 0.5)
        urgency = min(100.0, ai.need_ai_automation * 0.4 + ai.need_crm * 0.3 + business.buying_intent * 0.3)
        parts = [
            opportunity,
            budget,
            authority,
            need,
            timing,
            completeness,
            decision_makers,
            contact_avail,
            technology,
            growth,
            urgency,
        ]
        score = round(sum(parts) / len(parts), 2)
        if score >= 80 and verified_count >= 1 and committee_count >= 1:
            category = SalesReadinessCategory.FOUNDER_READY
        elif score >= 65:
            category = SalesReadinessCategory.SALES_READY
        elif score >= 50:
            category = SalesReadinessCategory.QUALIFIED
        elif score >= 30:
            category = SalesReadinessCategory.WARM
        else:
            category = SalesReadinessCategory.COLD
        return SalesReadinessReport(
            opportunity=round(opportunity, 2),
            budget=round(budget, 2),
            authority=round(authority, 2),
            need=round(need, 2),
            timing=round(timing, 2),
            data_completeness=round(completeness, 2),
            decision_makers=round(decision_makers, 2),
            contact_availability=round(contact_avail, 2),
            technology=round(technology, 2),
            growth=round(growth, 2),
            urgency=round(urgency, 2),
            confidence=round(min(95.0, profile_confidence * 0.5 + 40.0), 2),
            score=score,
            category=category,
            source="aip",
            last_verified=now,
            evidence=[f"score:{score}", f"category:{category.value}"],
        )


class IndustryBenchmarkEngine:
    BENCH = {
        "SaaS": ("51-200", 65.0, 55.0),
        "Healthcare": ("201-500", 50.0, 35.0),
        "Fintech": ("51-200", 70.0, 60.0),
        "Ecommerce": ("51-200", 60.0, 40.0),
    }

    def for_industry(self, industry: str | None) -> IndustryBenchmark:
        key = industry or "unknown"
        band, dig, ai = self.BENCH.get(key, ("unknown", 50.0, 40.0))
        return IndustryBenchmark(
            industry=key,
            avg_employee_band=band,
            avg_digital_maturity=dig,
            avg_ai_adoption=ai,
            evidence=[f"industry:{key}"],
        )
