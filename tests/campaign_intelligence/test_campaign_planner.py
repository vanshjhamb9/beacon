from uuid import uuid4

from campaign_intelligence import CampaignIntelligenceService, CampaignPlanner
from campaign_intelligence.models.types import CampaignInput, CampaignStatus, ChannelKind


def make_input(**overrides: object) -> CampaignInput:
    payload: dict[str, object] = {
        "company_id": uuid4(),
        "opportunity_id": uuid4(),
        "company_name": "Acme Logistics",
        "industry": "Logistics",
        "company_size": "51-200",
        "timezone": "America/New_York",
        "opportunity_score": 84.0,
        "opportunity_status": "high_intent",
        "opportunity_urgency": 70.0,
        "recommended_service": "AI Automation",
        "business_pain": "manual support workflows",
        "buyer_persona": "CTO",
        "sales_package": {
            "id": str(uuid4()),
            "review_status": "approved",
            "quality_scores": {"overall": 78.0},
            "style_variants": [
                {
                    "style": "technical",
                    "drafts": [
                        {
                            "kind": "email",
                            "style": "technical",
                            "title": "technical email",
                            "body": "Hello about manual support workflows",
                            "subject_lines": ["Acme idea", "Support ops", "Quick note"],
                        },
                        {
                            "kind": "follow_up_1",
                            "style": "technical",
                            "title": "fu1",
                            "body": "Follow up 1",
                            "subject_lines": [],
                        },
                        {
                            "kind": "follow_up_2",
                            "style": "technical",
                            "title": "fu2",
                            "body": "Follow up 2",
                            "subject_lines": [],
                        },
                        {
                            "kind": "linkedin",
                            "style": "technical",
                            "title": "li",
                            "body": "LinkedIn note",
                            "subject_lines": [],
                        },
                        {
                            "kind": "video_script",
                            "style": "technical",
                            "title": "video",
                            "body": "Video script",
                            "subject_lines": [],
                        },
                    ],
                }
            ],
            "evidence_chain": [
                {
                    "category": "pain",
                    "summary": "manual support workflows",
                    "source": "beacon_context",
                    "confidence": 80.0,
                }
            ],
        },
        "decision_discovery": {
            "best_outreach_sequence": [{"channel_kind": "founder_email", "value": "cto@acme.example"}],
            "buyer_match_confidence": 82.0,
            "overall_discovery_score": 80.0,
            "primary_decision_maker": {"name": "Sam", "role": "CTO", "confidence": 88.0},
        },
        "revenue": {"recommended_service": "AI Automation", "business_pain": "manual support workflows"},
        "verification": {"overall_readiness": 75.0, "trust_score": 80.0, "decision": "ready"},
        "outcomes": {"lifecycle_stage": "qualified", "contact_channels": []},
    }
    payload.update(overrides)
    return CampaignInput(**payload)  # type: ignore[arg-type]


def test_planner_builds_campaign_plan() -> None:
    plan = CampaignPlanner().plan(make_input())
    assert plan.company_name == "Acme Logistics"
    assert plan.status == CampaignStatus.NEEDS_REVIEW
    assert plan.primary_channel in set(ChannelKind)
    assert plan.follow_up_count >= 1
    assert plan.channel_choice_reason
    assert plan.timing_reason
    assert plan.message_selection_reason
    assert plan.evidence
    assert plan.expected_confidence > 0
    assert plan.plan_payload.get("schedule", {}).get("delivery_enabled") is False


def test_service_approve_pause_cancel() -> None:
    service = CampaignIntelligenceService()
    plan = service.create_plan(make_input())
    approved = service.approve(plan)
    assert approved.status == CampaignStatus.APPROVED
    paused = service.pause(approved)
    assert paused.status == CampaignStatus.PAUSED
    # cancel from paused
    cancelled = service.cancel(paused)
    assert cancelled.status == CampaignStatus.CANCELLED
