from uuid import uuid4

from sales_copilot import SalesCopilotPipeline
from sales_copilot.models.types import INSUFFICIENT, SalesCopilotInput


def make_input(**overrides: object) -> SalesCopilotInput:
    payload: dict[str, object] = {
        "company_id": uuid4(),
        "opportunity_id": uuid4(),
        "company_name": "Acme Logistics",
        "domain": "acmelogistics.example",
        "website": "https://acmelogistics.example",
        "industry": "Logistics",
        "opportunity_score": 86.0,
        "opportunity_status": "high_intent",
        "opportunity_narrative": "Support team scaling pressure",
        "business_pain": "manual support workflows",
        "recommended_service": "AI Automation",
        "buyer_persona": "CTO",
        "revenue": {
            "recommended_service": "AI Automation",
            "business_pain": "manual support workflows",
            "value_proposition": "Reduce ticket handling time",
            "conversation_angles": ["Automation for support ops"],
        },
        "lead_enrichment": {
            "technologies": [{"name": "Zendesk", "confidence": 80.0}],
            "jobs": [{"title": "Support Engineer", "confidence": 75.0}],
            "why_now": "Hiring into support while tickets grow",
            "company_profile": {"website": "https://acmelogistics.example"},
        },
        "verification": {"decision": "ready", "trust": {"score": 82.0}},
        "decision_makers": {
            "primary_decision_maker": {
                "name": "Sam Engineer",
                "role": "CTO",
                "confidence": 88.0,
                "evidence": "Team page",
            },
            "decision_makers": [
                {
                    "name": "Sam Engineer",
                    "role": "CTO",
                    "confidence": 88.0,
                    "evidence": "Team page",
                }
            ],
        },
        "context": {
            "dna": {"business_model": "B2B SaaS", "hiring_pattern": "Support expansion"},
            "pains": [{"description": "manual support workflows", "confidence": 80.0}],
        },
        "timeline": [
            {"summary": "Posted Support Engineer role", "event_type": "hiring", "confidence": 70.0},
            {"summary": "Evaluating automation tools", "event_type": "buying_intent", "confidence": 72.0},
        ],
        "evidence_chain": [
            {
                "category": "pain",
                "summary": "manual support workflows",
                "source": "beacon_context",
                "confidence": 80.0,
                "reference_id": "ev-1",
            }
        ],
    }
    payload.update(overrides)
    return SalesCopilotInput(**payload)  # type: ignore[arg-type]


def test_pipeline_builds_full_package_with_styles() -> None:
    result = SalesCopilotPipeline().process(make_input(), version=1)

    assert result.company_name == "Acme Logistics"
    assert result.version == 1
    assert len(result.sections) >= 18
    assert len(result.style_variants) == 6
    assert result.quality.overall > 0
    assert result.generation.prompt_version
    assert result.evidence_chain
    email = next(
        draft
        for variant in result.style_variants
        for draft in variant.drafts
        if draft.kind.value == "email" and draft.style.value == "professional"
    )
    assert "Acme Logistics" in email.body or "Sam Engineer" in email.body
    assert len(email.subject_lines) == 3


def test_pipeline_does_not_invent_missing_facts() -> None:
    result = SalesCopilotPipeline().process(
        make_input(
            business_pain="",
            recommended_service="",
            revenue={},
            lead_enrichment={},
            decision_makers={},
            context={},
            timeline=[],
            evidence_chain=[],
            opportunity_narrative="",
        )
    )

    tech = next(section for section in result.sections if section.key == "technology_stack")
    hiring = next(section for section in result.sections if section.key == "recent_hiring")
    makers = next(section for section in result.sections if section.key == "decision_makers")
    assert tech.content == INSUFFICIENT
    assert hiring.content == INSUFFICIENT
    assert makers.content == INSUFFICIENT


def test_regeneration_version_is_immutable_input() -> None:
    first = SalesCopilotPipeline().process(make_input(), version=1)
    second = SalesCopilotPipeline().process(make_input(), version=2)
    assert first.version == 1
    assert second.version == 2
    assert first.sections[0].content  # still intact
