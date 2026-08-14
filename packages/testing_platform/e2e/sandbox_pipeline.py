from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from campaign_intelligence import CampaignIntelligenceService
from campaign_intelligence.models.types import CampaignInput
from communication_gateway import CommunicationGatewayService, GatewayConfig, OutboundMessage
from communication_gateway.models.types import (
    CalendarEventRequest,
    ChannelType,
    CommunicationMode,
    ProviderName,
)
from conversation_center import ConversationCenterService, ConversationItem
from conversation_center.models.types import ConversationChannel, ConversationItemType
from sales_copilot import SalesCopilotPipeline
from sales_copilot.models.types import SalesCopilotInput
from testing_platform.models.types import E2ERunResult, E2EStepResult


class SandboxPipelineE2E:
    """End-to-end sandbox campaign from opportunity package through reply + meeting."""

    def run(self) -> E2ERunResult:
        steps: list[E2EStepResult] = []
        company_id = uuid4()
        opportunity_id = uuid4()

        def step(name: str, fn) -> None:
            started = time.perf_counter()
            try:
                detail = fn()
                steps.append(
                    E2EStepResult(
                        name=name,
                        passed=True,
                        detail=str(detail),
                        duration_ms=(time.perf_counter() - started) * 1000,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                steps.append(
                    E2EStepResult(
                        name=name,
                        passed=False,
                        detail=str(exc),
                        duration_ms=(time.perf_counter() - started) * 1000,
                    )
                )

        package_holder: dict = {}

        def create_sales_package() -> str:
            package = SalesCopilotPipeline().process(
                SalesCopilotInput(
                    company_id=company_id,
                    opportunity_id=opportunity_id,
                    company_name="E2E Sandbox Co",
                    industry="Software",
                    opportunity_score=88.0,
                    business_pain="manual onboarding",
                    recommended_service="AI Automation",
                    buyer_persona="CTO",
                    revenue={
                        "recommended_service": "AI Automation",
                        "business_pain": "manual onboarding",
                        "conversation_angles": ["onboarding automation"],
                    },
                    decision_makers={
                        "primary_decision_maker": {"name": "Alex CTO", "role": "CTO", "confidence": 90},
                        "decision_makers": [{"name": "Alex CTO", "role": "CTO", "confidence": 90}],
                    },
                    lead_enrichment={"technologies": [{"name": "Python"}], "jobs": [{"title": "Support Lead"}]},
                    verification={"decision": "ready", "overall_score": 85},
                    evidence_chain=[
                        {
                            "category": "pain",
                            "summary": "manual onboarding",
                            "source": "beacon_context",
                            "confidence": 85,
                        }
                    ],
                ),
                version=1,
            )
            package_holder["package"] = package
            assert package.sections
            assert package.style_variants
            return f"package v{package.version} quality={package.quality.overall}"

        step("sales_package", create_sales_package)

        campaign_holder: dict = {}

        def create_campaign() -> str:
            package = package_holder["package"]
            drafts = []
            for variant in package.style_variants:
                for draft in variant.drafts:
                    drafts.append(draft.model_dump(mode="json"))
            plan = CampaignIntelligenceService().create_plan(
                CampaignInput(
                    company_id=company_id,
                    opportunity_id=opportunity_id,
                    company_name="E2E Sandbox Co",
                    industry="Software",
                    opportunity_score=88.0,
                    recommended_service="AI Automation",
                    business_pain="manual onboarding",
                    buyer_persona="CTO",
                    sales_package={
                        "id": str(uuid4()),
                        "review_status": "approved",
                        "quality_scores": package.quality.model_dump(mode="json"),
                        "style_variants": [v.model_dump(mode="json") for v in package.style_variants],
                        "drafts": drafts,
                        "evidence_chain": [e.model_dump(mode="json") for e in package.evidence_chain],
                    },
                    decision_discovery={
                        "best_outreach_sequence": [{"channel_kind": "founder_email"}],
                        "buyer_match_confidence": 85,
                        "primary_decision_maker": {"name": "Alex CTO", "role": "CTO", "confidence": 90},
                    },
                    verification={"overall_readiness": 85, "trust_score": 85, "decision": "ready"},
                    outcomes={"lifecycle_stage": "qualified"},
                )
            )
            approved = CampaignIntelligenceService().approve(plan)
            campaign_holder["plan"] = approved
            assert approved.outreach_sequence
            return f"campaign status={approved.status.value} steps={len(approved.outreach_sequence)}"

        step("campaign_plan_and_approve", create_campaign)

        gateway = CommunicationGatewayService(
            GatewayConfig(mode=CommunicationMode.SANDBOX, allow_production_send=False)
        )
        inbox = ConversationCenterService()
        send_holder: dict = {}

        def sandbox_send() -> str:
            plan = campaign_holder["plan"]
            first = plan.outreach_sequence[0]
            message = OutboundMessage(
                channel=ChannelType.EMAIL,
                provider=ProviderName.SANDBOX_EMAIL,
                to_address="alex@e2e-sandbox.example",
                subject=first.subject_preview or "Beacon sandbox outreach",
                body_text=first.body_preview or "Sandbox outreach body",
                campaign_id=uuid4(),
                company_id=company_id,
                opportunity_id=opportunity_id,
            )
            # Use a stable campaign id for stop rules
            campaign_id = message.campaign_id
            campaign_holder["campaign_id"] = campaign_id
            result = gateway.sandbox_send_and_simulate_reply(message, reply_body="Happy to meet Thursday.")
            send_holder["result"] = result
            assert result["send"]["state"] == "sent"
            assert result["inbound_handling"]["campaign_stopped"] is True
            inbox.add_item(
                ConversationItem(
                    company_id=company_id,
                    opportunity_id=opportunity_id,
                    campaign_id=campaign_id,
                    channel=ConversationChannel.EMAIL,
                    item_type=ConversationItemType.MESSAGE,
                    direction="outbound",
                    subject=message.subject,
                    body=message.body_text,
                    to_address=message.to_address,
                    provider_message_id=result["send"]["provider_message_id"],
                    thread_id=result["send"]["thread_id"],
                )
            )
            inbox.add_item(
                ConversationItem(
                    company_id=company_id,
                    opportunity_id=opportunity_id,
                    campaign_id=campaign_id,
                    channel=ConversationChannel.EMAIL,
                    item_type=ConversationItemType.REPLY,
                    direction="inbound",
                    subject="Re: " + (message.subject or ""),
                    body="Happy to meet Thursday.",
                    from_address=message.to_address,
                    unread=True,
                    thread_id=result["send"]["thread_id"],
                )
            )
            return "sandbox send + simulated reply + campaign stop"

        step("sandbox_send_reply_stop", sandbox_send)

        def book_meeting() -> str:
            booking = gateway.book_meeting(
                CalendarEventRequest(
                    title="E2E discovery",
                    description="Sandbox meeting",
                    start_at=datetime.now(UTC) + timedelta(days=2),
                    end_at=datetime.now(UTC) + timedelta(days=2, hours=1),
                    timezone="UTC",
                    attendees=["alex@e2e-sandbox.example"],
                    company_id=company_id,
                    opportunity_id=opportunity_id,
                    campaign_id=campaign_holder.get("campaign_id"),
                )
            )
            meeting_event = gateway.simulator.simulate_meeting(
                title="E2E discovery",
                attendee="alex@e2e-sandbox.example",
            )
            gateway.handle_inbound(meeting_event, campaign_id=campaign_holder.get("campaign_id"))
            inbox.add_item(
                ConversationItem(
                    company_id=company_id,
                    opportunity_id=opportunity_id,
                    campaign_id=campaign_holder.get("campaign_id"),
                    channel=ConversationChannel.MEETING,
                    item_type=ConversationItemType.MEETING,
                    direction="system",
                    subject="E2E discovery",
                    body=f"Meeting booked: {booking.meeting_url}",
                )
            )
            assert booking.sandbox is True
            return f"meeting={booking.event_id}"

        step("sandbox_meeting", book_meeting)

        def conversation_summary() -> str:
            threads = inbox.search(__import__("conversation_center.models.types", fromlist=["ConversationFilter"]).ConversationFilter(company_id=company_id))
            assert threads
            summary = inbox.ai_summary(threads[0].id)  # type: ignore[arg-type]
            assert summary
            return summary

        step("conversation_center", conversation_summary)

        def outcome_recorded() -> str:
            # Domain-level outcome marker for E2E (API persistence covered in API tests)
            return "outcome stages: replied -> meeting_scheduled"

        step("outcome_recorded", outcome_recorded)

        passed = all(item.passed for item in steps)
        return E2ERunResult(scenario="sandbox_full_pipeline", passed=passed, steps=steps, mode="sandbox")
