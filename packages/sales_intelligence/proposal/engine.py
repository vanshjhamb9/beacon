from __future__ import annotations

from sales_intelligence.models.types import OfferType, ProposalIntelligence, SalesIntelligenceInput


class ProposalIntelligenceEngine:
    def generate(
        self,
        item: SalesIntelligenceInput,
        *,
        primary_offer: OfferType | None = None,
        expected_value: str | None = None,
    ) -> ProposalIntelligence:
        offer = primary_offer.value if primary_offer else (item.recommended_service or "Custom engagement")
        employees = item.employee_count or 50
        weeks = 6 if employees < 50 else (10 if employees < 200 else 14)
        budget = expected_value or item.expected_budget or "$25k–$55k"
        roi = "3–6x in 12 months" if "automation" in offer.lower() or "ai" in offer.lower() else "2–4x in 12 months"
        outline = [
            "Executive summary",
            "Current-state diagnosis",
            f"Recommended solution: {offer}",
            "Scope & deliverables",
            "Timeline & milestones",
            "Commercials & ROI",
            "Risks & mitigations",
            "Next steps",
        ]
        scope = [
            f"Discovery and stakeholder alignment for {item.company_name}",
            f"Design and deliver {offer}",
            "Integrate with existing tools where applicable",
            "Enable team with runbooks and handover",
        ]
        deliverables = [
            "Discovery report",
            "Solution architecture",
            "Working MVP / release",
            "Admin + operator documentation",
            "30-day support window",
        ]
        architecture = [
            "Ingestion / event layer",
            "Business logic / automation layer",
            "LLM / decision layer (optional)",
            "Dashboard / operator UI",
            "Observability + audit trail",
        ]
        plan = [
            f"Week 1–2: discovery + architecture for {offer}",
            "Week 3–4: core build + integrations",
            f"Week 5–{weeks}: hardening, UAT, rollout",
        ]
        risks = [
            {"risk": "Scope creep", "mitigation": "Fixed MVP definition + change-control"},
            {"risk": "Integration delay", "mitigation": "Early API access + sandbox"},
            {"risk": "Adoption risk", "mitigation": "Training + office hours"},
        ]
        return ProposalIntelligence(
            proposal_outline=outline,
            scope=scope,
            timeline=f"{weeks} weeks",
            deliverables=deliverables,
            architecture=architecture,
            budget_range=budget,
            roi_estimate=roi,
            implementation_plan=plan,
            risk_assessment=risks,
            evidence=[f"offer:{offer}", f"employees:{employees}", f"budget:{budget}"],
        )
