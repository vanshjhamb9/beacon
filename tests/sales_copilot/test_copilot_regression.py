from uuid import uuid4

from sales_copilot import SalesCopilotPipeline, SalesCopilotService
from sales_copilot.models.types import DraftKind, OutreachStyle
from tests.sales_copilot.test_copilot_pipeline import make_input


REQUIRED_SECTIONS = {
    "executive_summary",
    "company_overview",
    "business_model",
    "current_situation",
    "pain_points",
    "growth_signals",
    "buying_signals",
    "technology_stack",
    "recent_hiring",
    "decision_makers",
    "recommended_service",
    "value_proposition",
    "conversation_strategy",
    "opening_angle",
    "things_to_mention",
    "things_to_avoid",
    "possible_objections",
    "suggested_responses",
    "meeting_objectives",
}


def test_service_wrapper_matches_pipeline_contract() -> None:
    service = SalesCopilotService()
    package = service.generate(make_input(company_id=uuid4(), opportunity_id=uuid4()), version=3)
    assert package.version == 3
    assert {section.key for section in package.sections} == REQUIRED_SECTIONS
    assert {variant.style for variant in package.style_variants} == set(OutreachStyle)
    kinds = {draft.kind for variant in package.style_variants for draft in variant.drafts}
    assert DraftKind.EMAIL in kinds
    assert DraftKind.FOLLOW_UP_3 in kinds
    assert "Insufficient verified information" not in package.sections[0].content or package.business_pain


def test_no_send_side_effects_in_package_payload() -> None:
    package = SalesCopilotPipeline().process(make_input())
    blob = str(package.package_payload).lower() + " ".join(section.content.lower() for section in package.sections)
    assert "message sent" not in blob
    assert "email delivered" not in blob
