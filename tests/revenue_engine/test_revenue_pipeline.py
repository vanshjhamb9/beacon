from uuid import uuid4

from revenue_engine import RevenuePipeline, default_service_catalog
from revenue_engine.models.types import BudgetRange, ProjectSize, RevenueOpportunityInput


def make_input(**overrides: object) -> RevenueOpportunityInput:
    payload = {
        "company_id": uuid4(),
        "company_name": "Acme Logistics",
        "opportunity_id": uuid4(),
        "opportunity_score": 82.0,
        "urgency_score": 74.0,
        "confidence_score": 80.0,
        "recommendation": "contact_within_7_days",
        "narrative": "Acme Logistics shows rising automation demand after expansion signals.",
        "industry": "logistics",
        "business_model": "b2b",
        "company_stage": "scaling",
        "technology_stack": ["Salesforce", "OpenAI"],
        "pains": [{"category": "automation", "value": "manual ops workflows", "confidence": 84.0}],
        "goals": [{"category": "efficiency", "value": "reduce cycle time", "confidence": 78.0}],
        "contexts": [{"automation_readiness": 82.0, "operational_pressure": 79.0}],
        "opportunity_evidence": [
            {"category": "automation", "summary": "Ops team seeking workflow automation", "confidence": 84.0}
        ],
        "knowledge_node_ids": [uuid4()],
        "quality_score": 88.0,
        "services": default_service_catalog(),
    }
    payload.update(overrides)
    return RevenueOpportunityInput(**payload)  # type: ignore[arg-type]


def test_revenue_pipeline_returns_explainable_recommendation() -> None:
    result = RevenuePipeline().process(make_input())

    assert result.primary_service.service.name
    assert result.playbook.business_pain
    assert result.playbook.recommended_service == result.primary_service.service.name
    assert result.playbook.decision_maker
    assert result.playbook.conversation_angle
    assert result.revenue_estimate.project_size in {
        ProjectSize.SMALL,
        ProjectSize.MEDIUM,
        ProjectSize.LARGE,
        ProjectSize.ENTERPRISE,
    }
    assert result.revenue_estimate.estimated_budget_range in {
        BudgetRange.SMALL,
        BudgetRange.MEDIUM,
        BudgetRange.LARGE,
        BudgetRange.ENTERPRISE,
    }
    assert result.buyer_personas
    assert result.deal_prediction.priority_level
    assert result.confidence >= 35.0
    assert result.processing_latency_ms >= 0.0
    assert "why_now" in result.evidence
    assert result.reasoning


def test_revenue_pipeline_prefers_ai_automation_for_operations_pain() -> None:
    result = RevenuePipeline().process(make_input())

    assert result.primary_service.service.service_key in {
        "ai_automation",
        "custom_ai_development",
        "ai_agents",
        "comai",
        "api_integration",
        "erp_development",
    }
