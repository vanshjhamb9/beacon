from uuid import uuid4

from sales_copilot.context.assembler import ContextAssembler
from sales_copilot.evaluation.grounding import GroundingValidator
from sales_copilot.evaluation.scorer import QualityScorer
from sales_copilot.generation.outreach_generator import OutreachGenerator
from sales_copilot.generation.package_generator import PackageGenerator
from sales_copilot.llm.factory import LLMProviderConfig, LLMProviderFactory
from sales_copilot.llm.grounded import GroundedProvider
from sales_copilot.models.types import (
    GenerationMetadata,
    INSUFFICIENT,
    LLMProviderName,
    LLMRequest,
    OutreachStyle,
    QualityScores,
    ReviewAction,
    SalesCopilotInput,
    SalesIntelligencePackage,
)
from sales_copilot.prompting.versions import CURRENT_PROMPT_VERSION, get_prompt_version
from sales_copilot.templates.styles import STYLE_GUIDANCE


def _facts() -> dict:
    item = SalesCopilotInput(
        company_id=uuid4(),
        opportunity_id=uuid4(),
        company_name="Nova Health",
        business_pain="claims backlog",
        recommended_service="AI Agents",
        opportunity_score=77.0,
        lead_enrichment={"technologies": [{"name": "Salesforce"}], "jobs": [{"title": "Claims Analyst"}]},
        decision_makers={
            "primary_decision_maker": {"name": "Taylor Ops", "role": "COO", "confidence": 80.0},
            "decision_makers": [{"name": "Taylor Ops", "role": "COO", "confidence": 80.0}],
        },
        evidence_chain=[{"category": "pain", "summary": "claims backlog", "source": "beacon_context", "confidence": 80}],
    )
    return ContextAssembler().assemble(item)


def test_context_assembler_builds_evidence() -> None:
    facts = _facts()
    assert facts["company_name"] == "Nova Health"
    assert facts["technology_stack"]
    assert facts["decision_makers"]
    assert facts["evidence"]


def test_package_generator_sections_and_attribution() -> None:
    sections = PackageGenerator().generate(_facts())
    keys = {section.key for section in sections}
    assert "executive_summary" in keys
    assert "meeting_objectives" in keys
    assert all(section.attribution.section for section in sections)


def test_outreach_generator_all_styles_and_draft_kinds() -> None:
    variants = OutreachGenerator().generate_all_styles(_facts())
    assert len(variants) == len(OutreachStyle)
    professional = next(item for item in variants if item.style == OutreachStyle.PROFESSIONAL)
    kinds = {draft.kind.value for draft in professional.drafts}
    assert {"email", "subject_line", "linkedin", "whatsapp", "video_script", "meeting_agenda"}.issubset(kinds)
    assert "follow_up_1" in kinds
    assert "follow_up_3" in kinds


def test_quality_scorer_and_grounding() -> None:
    facts = _facts()
    sections = PackageGenerator().generate(facts)
    variants = OutreachGenerator().generate_all_styles(facts)
    package = SalesIntelligencePackage(
        company_id=uuid4(),
        opportunity_id=uuid4(),
        company_name="Nova Health",
        opportunity_score=77.0,
        recommended_service="AI Agents",
        business_pain="claims backlog",
        version=1,
        sections=sections,
        style_variants=variants,
        evidence_chain=list(facts["evidence"]),
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
    scored = QualityScorer().score(package)
    assert scored.overall > 0
    assert scored.evidence_coverage > 0
    assert GroundingValidator().is_safe(package.model_copy(update={"quality": scored}))


def test_llm_factory_falls_back_to_grounded() -> None:
    factory = LLMProviderFactory(LLMProviderConfig(provider=LLMProviderName.OPENAI, openai_api_key=None))
    provider = factory.create(LLMProviderName.OPENAI)
    assert isinstance(provider, GroundedProvider)
    response = provider.complete(
        LLMRequest(system_prompt="sys", user_prompt="hello evidence", model="grounded-v1", temperature=0.2)
    )
    assert response.provider == LLMProviderName.GROUNDED
    assert "hello evidence" in response.content


def test_prompt_version_registry() -> None:
    prompt = get_prompt_version()
    assert prompt.version == CURRENT_PROMPT_VERSION
    assert "Insufficient verified information" in prompt.system_prompt
    assert ReviewAction.APPROVE.value == "approve"
    assert OutreachStyle.FOUNDER_TO_FOUNDER in STYLE_GUIDANCE
    assert INSUFFICIENT
