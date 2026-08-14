from __future__ import annotations

from autonomous_sales_agent.models.types import AutonomousSalesAgentInput, CaseStudyRecommendation


CASE_LIBRARY: dict[str, tuple[str, str]] = {
    "AI Automation": ("Ops automation cut manual handoffs 40%", "automation"),
    "CRM": ("CRM redesign improved forecast accuracy", "crm"),
    "SaaS": ("Multi-tenant SaaS MVP shipped in 8 weeks", "saas"),
    "Healthcare": ("Clinical intake automation under compliance constraints", "healthcare"),
    "Manufacturing": ("Production ops workflow automation", "manufacturing"),
    "Education": ("Admissions assistant reduced response time", "education"),
    "Hospitality": ("Guest support deflection with WhatsApp AI", "hospitality"),
    "Construction": ("Field ops reporting automation", "construction"),
    "Retail": ("DTC support cost reduction case study", "retail"),
    "Logistics": ("Dispatch coordination automation", "logistics"),
}


class CaseStudyRecommendationEngine:
    def recommend(self, item: AutonomousSalesAgentInput) -> CaseStudyRecommendation:
        industry = (item.industry or "").strip()
        service = (item.recommended_service or "").lower()
        key = None
        relevance = 70.0
        why = "Default proof pack"
        if industry:
            for name in CASE_LIBRARY:
                if name.lower() == industry.lower() or name.lower() in industry.lower():
                    key = name
                    relevance = 92.0
                    why = f"Industry match: {industry}"
                    break
        if key is None:
            for name, (_, tag) in CASE_LIBRARY.items():
                if tag in service or name.lower() in service:
                    key = name
                    relevance = 88.0
                    why = f"Service match: {item.recommended_service}"
                    break
        if key is None:
            if any("support" in p.lower() or "manual" in p.lower() for p in item.pains):
                key = "AI Automation"
                relevance = 80.0
                why = "Pain pattern matches automation case study"
            else:
                key = "SaaS"
                relevance = 72.0
                why = "Fallback growth-stage SaaS proof"
        title, _ = CASE_LIBRARY[key]
        return CaseStudyRecommendation(
            industry_key=key,
            title=title,
            relevance=relevance,
            why=why,
            evidence=[f"key:{key}", f"industry:{industry or 'n/a'}", f"service:{item.recommended_service or 'n/a'}"],
        )
