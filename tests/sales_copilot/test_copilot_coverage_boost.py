from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from sales_copilot import api as sales_api
from sales_copilot import repository as sales_repo
from sales_copilot import storage as sales_storage
from sales_copilot.context.assembler import ContextAssembler
from sales_copilot.evaluation.grounding import GroundingValidator
from sales_copilot.generation.grounding_helpers import evidence_or_insufficient
from sales_copilot.generation.package_generator import PackageGenerator
from sales_copilot.llm.anthropic_adapter import AnthropicAdapter
from sales_copilot.llm.base import BaseLLMAdapter
from sales_copilot.llm.gemini_adapter import GeminiAdapter
from sales_copilot.llm.grounded import GroundedProvider
from sales_copilot.llm.openrouter_adapter import OpenRouterAdapter
from sales_copilot.models.types import (
    GenerationMetadata,
    INSUFFICIENT,
    LLMProviderName,
    LLMRequest,
    OutreachStyle,
    QualityScores,
    SalesCopilotInput,
    SalesIntelligencePackage,
    SectionAttribution,
    IntelligenceSection,
)
from sales_copilot.prompting.versions import CURRENT_PROMPT_VERSION
from sales_copilot.templates.styles import style_label


def test_stub_modules_importable() -> None:
    assert sales_api.__all__ == []
    assert sales_storage.__all__ == []
    assert sales_repo.SalesCopilotRepositoryProtocol


def test_style_label_and_helpers() -> None:
    assert style_label(OutreachStyle.FOUNDER_TO_FOUNDER) == "Founder To Founder"
    assert evidence_or_insufficient(None) == INSUFFICIENT
    assert evidence_or_insufficient("  ") == INSUFFICIENT
    assert "Acme" in evidence_or_insufficient([{"name": "Acme", "role": "CEO"}])


def test_assembler_edge_paths() -> None:
    item = SalesCopilotInput(
        company_id=uuid4(),
        opportunity_id=uuid4(),
        company_name="Edge Co",
        opportunity_score=50.0,
        company={"primary_domain": "edge.example", "industry": "Software"},
        lead_enrichment={
            "company_profile": {"website": "https://edge.example", "industry": "Software", "business_model": "B2B"},
            "technology_stack": ["Python"],
            "recent_hiring": ["Platform Engineer"],
            "signals": [{"summary": "buying evaluation", "type": "buying"}],
            "pain_points": ["latency"],
        },
        revenue={"pain_points": [{"description": "latency"}], "conversation_angles": ["latency"]},
        context={
            "dna": {"business_model": "B2B", "hiring_pattern": "Platform growth"},
            "hiring_pattern": "Platform growth",
            "technologies": [{"name": "Postgres"}],
            "profile": {"business_model": "B2B"},
        },
        opportunity={"signals": ["growth expansion"]},
        knowledge_graph={"nodes": [{"id": "n1", "label": "Edge Co", "node_type": "company"}]},
        timeline=[{"summary": "funding round", "event_type": "funding", "confidence": 70}],
        verification={"decision": "ready", "id": str(uuid4()), "overall_score": 80},
        decision_makers={
            "decision_makers": [
                {"name": "Pat", "role": "CTO", "confidence": 70, "id": "m1", "source_url": "https://edge.example/team"}
            ]
        },
        evidence_chain=[{"category": "evidence", "summary": "", "source": "beacon_context"}],
    )
    facts = ContextAssembler().assemble(item)
    assert facts["domain"]
    assert facts["technology_stack"]
    assert facts["recent_hiring"]
    assert facts["growth_signals"] or facts["buying_signals"]
    sections = PackageGenerator().generate(facts)
    assert any(section.key == "business_model" for section in sections)


def test_remaining_llm_adapters() -> None:
    req = LLMRequest(system_prompt="s", user_prompt="u", model="m", temperature=0.2)

    anthropic_payload = {
        "model": "claude",
        "content": [{"type": "text", "text": "hi"}],
        "usage": {"input_tokens": 3, "output_tokens": 2},
    }
    gemini_payload = {
        "candidates": [{"content": {"parts": [{"text": "hi"}]}}],
        "usageMetadata": {"promptTokenCount": 3, "candidatesTokenCount": 2, "totalTokenCount": 5},
    }
    openrouter_payload = {
        "model": "auto",
        "choices": [{"message": {"content": "hi"}}],
        "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5, "cost": 0.01},
    }

    for module, cls, payload, key in (
        ("sales_copilot.llm.anthropic_adapter", AnthropicAdapter, anthropic_payload, "key"),
        ("sales_copilot.llm.gemini_adapter", GeminiAdapter, gemini_payload, "key"),
        ("sales_copilot.llm.openrouter_adapter", OpenRouterAdapter, openrouter_payload, "key"),
    ):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = payload
        with patch(f"{module}.httpx.Client") as client_cls:
            client = client_cls.return_value.__enter__.return_value
            client.post.return_value = mock_response
            result = cls(api_key=key).complete(req)
        assert result.content == "hi"

    assert GroundedProvider().default_model() == "grounded-v1"
    with pytest.raises(NotImplementedError):
        BaseLLMAdapter.default_model(BaseLLMAdapter())  # type: ignore[misc]
    with pytest.raises(NotImplementedError):
        BaseLLMAdapter.complete(BaseLLMAdapter(), req)  # type: ignore[misc]


def test_grounding_validator_edge_cases() -> None:
    package = SalesIntelligencePackage(
        company_id=uuid4(),
        opportunity_id=uuid4(),
        company_name="Safe",
        opportunity_score=10.0,
        recommended_service="",
        business_pain="",
        version=1,
        sections=[
            IntelligenceSection(
                key="x",
                title="X",
                content="Invented Soft product claim",
                attribution=SectionAttribution(section="x", grounded=False, evidence_summaries=[]),
            )
        ],
        style_variants=[],
        evidence_chain=[],
        quality=QualityScores(
            personalization=0,
            evidence_coverage=0,
            readability=0,
            professional_tone=0,
            length=0,
            call_to_action=0,
            confidence=0,
            overall=0,
        ),
        generation=GenerationMetadata(
            prompt_version=CURRENT_PROMPT_VERSION,
            llm_provider=LLMProviderName.GROUNDED,
            model="grounded-v1",
            temperature=0.2,
        ),
    )
    issues = GroundingValidator().validate(package)
    assert issues
