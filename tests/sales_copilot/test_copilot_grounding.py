from uuid import uuid4

from sales_copilot import SalesCopilotPipeline
from sales_copilot.evaluation.grounding import GroundingValidator
from sales_copilot.models.types import INSUFFICIENT, SalesCopilotInput


def test_every_section_has_attribution() -> None:
    package = SalesCopilotPipeline().process(
        SalesCopilotInput(
            company_id=uuid4(),
            opportunity_id=uuid4(),
            company_name="Grounded Co",
            business_pain="slow onboarding",
            recommended_service="AI Automation",
            opportunity_score=70.0,
            evidence_chain=[
                {
                    "category": "pain",
                    "summary": "slow onboarding",
                    "source": "beacon_context",
                    "confidence": 75.0,
                    "reference_id": "p1",
                }
            ],
            decision_makers={
                "decision_makers": [{"name": "Alex", "role": "CEO", "confidence": 70.0}],
            },
        )
    )
    for section in package.sections:
        assert section.attribution.section == section.key
        if section.content != INSUFFICIENT:
            assert section.attribution.grounded or section.attribution.evidence_summaries or section.key in {
                "things_to_avoid",
                "possible_objections",
                "suggested_responses",
                "meeting_objectives",
            }


def test_grounding_validator_flags_fabrication_pattern() -> None:
    package = SalesCopilotPipeline().process(
        SalesCopilotInput(
            company_id=uuid4(),
            opportunity_id=uuid4(),
            company_name="Safe Co",
            opportunity_score=60.0,
        )
    )
    poisoned = package.sections[0].model_copy(update={"content": "We found that they secretly use guaranteed ROI tools."})
    bad = package.model_copy(update={"sections": [poisoned, *package.sections[1:]]})
    issues = GroundingValidator().validate(bad)
    assert issues
