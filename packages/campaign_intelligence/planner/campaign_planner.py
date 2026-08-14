from __future__ import annotations

from typing import Any

from campaign_intelligence.channels.catalog import get_channel
from campaign_intelligence.models.types import (
    CampaignInput,
    CampaignPlan,
    CampaignPriority,
    CampaignStatus,
    CampaignStepPlan,
    ChannelKind,
    EvidenceItem,
    StepKind,
)
from campaign_intelligence.planner.message_selector import MessageSelector
from campaign_intelligence.scheduler.rules import ScheduleEngine
from campaign_intelligence.templates.defaults import CHANNEL_RANK_DEFAULT, DEFAULT_SEQUENCE_DELAYS, default_schedule


class CampaignPlanner:
    def __init__(
        self,
        *,
        selector: MessageSelector | None = None,
        scheduler: ScheduleEngine | None = None,
    ) -> None:
        self.selector = selector or MessageSelector()
        self.scheduler = scheduler or ScheduleEngine()

    def plan(self, item: CampaignInput) -> CampaignPlan:
        package = dict(item.sales_package or {})
        decision = dict(item.decision_discovery or {})
        verification = dict(item.verification or {})
        outcomes = dict(item.outcomes or {})

        primary, secondary, channel_reason = self._choose_channels(item, decision)
        priority = self._priority(item)
        style = self.selector.preferred_style(
            buyer_persona=item.buyer_persona or decision.get("buyer_persona"),
            industry=item.industry,
            company_size=item.company_size,
            recommended_service=item.recommended_service,
            package_styles=self._package_styles(package),
        )
        delays = list(DEFAULT_SEQUENCE_DELAYS)
        # Reduce follow-ups for lower readiness
        readiness = float(verification.get("overall_readiness") or verification.get("trust_score") or 50.0)
        if readiness < 50:
            delays = delays[:2]
        elif readiness < 70:
            delays = delays[:3]

        rules = self.scheduler.normalize_rules(default_schedule(timezone=item.timezone), timezone=item.timezone)
        planned_times = self.scheduler.plan_step_times(rules=rules, delay_hours=delays)
        timing_reason = self.scheduler.timing_reason(rules)

        steps: list[CampaignStepPlan] = []
        message_reasons: list[str] = []
        for idx, delay in enumerate(delays):
            if idx == 0:
                channel = primary
                kind = StepKind.INITIAL
                follow_idx = None
            elif idx == len(delays) - 1 and secondary == ChannelKind.CALENDAR_INVITATION:
                channel = ChannelKind.CALENDAR_INVITATION
                kind = StepKind.MEETING_INVITE
                follow_idx = None
            else:
                channel = secondary or primary
                kind = StepKind.FOLLOW_UP
                follow_idx = idx - 1

            if channel == ChannelKind.PERSONALIZED_VIDEO:
                kind = StepKind.VIDEO
            if channel == ChannelKind.PHONE_CALL:
                kind = StepKind.CALL

            draft, msg_reason = self.selector.select_draft(
                sales_package=package,
                channel=channel if kind != StepKind.FOLLOW_UP else primary,
                style=style,
                follow_up_index=follow_idx if kind == StepKind.FOLLOW_UP else None,
            )
            # Follow-ups stay on primary channel drafts
            if kind == StepKind.FOLLOW_UP:
                channel = primary
            message_reasons.append(msg_reason)
            subjects = draft.get("subject_lines") or []
            steps.append(
                CampaignStepPlan(
                    sequence=idx + 1,
                    kind=kind,
                    channel=channel,
                    delay_hours=delay,
                    draft_kind=str(draft.get("kind") or ""),
                    draft_style=str(draft.get("style") or style),
                    subject_preview=str(subjects[0] if subjects else ""),
                    body_preview=str(draft.get("body") or "")[:500],
                    message_selection_reason=msg_reason,
                    timing_reason=f"Step {idx + 1} planned at {planned_times[idx].isoformat()} ({rules.timezone}).",
                    confidence=self._step_confidence(item, readiness, draft),
                    evidence=self._step_evidence(item, channel, draft),
                    sales_draft_ref={
                        "kind": draft.get("kind"),
                        "style": draft.get("style"),
                        "title": draft.get("title"),
                    },
                )
            )

        evidence = self._campaign_evidence(item, primary, secondary)
        expected_confidence = round(
            min(
                100.0,
                (item.opportunity_score * 0.35)
                + (readiness * 0.25)
                + (float(decision.get("buyer_match_confidence") or decision.get("overall_discovery_score") or 40.0) * 0.2)
                + (float((package.get("quality_scores") or package.get("quality") or {}).get("overall") or 50.0) * 0.2),
            ),
            2,
        )
        sales_package_id = package.get("id")
        try:
            from uuid import UUID as _UUID

            package_uuid = _UUID(str(sales_package_id)) if sales_package_id else None
        except Exception:
            package_uuid = None

        return CampaignPlan(
            company_id=item.company_id,
            opportunity_id=item.opportunity_id,
            sales_package_id=package_uuid,
            company_name=item.company_name,
            status=CampaignStatus.NEEDS_REVIEW,
            priority=priority,
            primary_channel=primary,
            secondary_channel=secondary,
            outreach_sequence=steps,
            follow_up_count=max(0, len(steps) - 1),
            delay_hours_between_messages=delays,
            expected_confidence=expected_confidence,
            channel_choice_reason=channel_reason,
            timing_reason=timing_reason,
            message_selection_reason=message_reasons[0] if message_reasons else "No draft selected.",
            schedule_rules=rules,
            recommended_service=item.recommended_service,
            business_pain=item.business_pain,
            buyer_persona=item.buyer_persona,
            industry=item.industry,
            communication_style=style,
            evidence=evidence,
            quality={
                "expected_confidence": expected_confidence,
                "verification_readiness": readiness,
                "opportunity_score": item.opportunity_score,
                "delivery_enabled": False,
            },
            plan_payload={
                "schedule": self.scheduler.as_payload(rules, planned_times),
                "outcomes_signal": {
                    "lifecycle_stage": outcomes.get("lifecycle_stage"),
                    "prior_contact_channels": outcomes.get("contact_channels") or [],
                },
                "channel_capabilities": {
                    "primary": get_channel(primary).model_dump(mode="json"),
                    "secondary": get_channel(secondary).model_dump(mode="json") if secondary else None,
                },
                "message_selection_reasons": message_reasons,
            },
        )

    def _choose_channels(
        self, item: CampaignInput, decision: dict[str, Any]
    ) -> tuple[ChannelKind, ChannelKind | None, str]:
        sequence = decision.get("best_outreach_sequence") or []
        channels_hint: list[str] = []
        for step in sequence:
            if isinstance(step, dict):
                channels_hint.append(str(step.get("channel_kind") or step.get("kind") or "").lower())

        primary = ChannelKind.EMAIL
        if any("linkedin" in hint for hint in channels_hint):
            primary = ChannelKind.LINKEDIN
        if any("email" in hint or "@" in hint for hint in channels_hint):
            primary = ChannelKind.EMAIL
        if any("whatsapp" in hint or "phone" in hint for hint in channels_hint) and item.opportunity_score >= 80:
            # Prefer email still as primary; whatsapp as secondary
            pass

        # Persona/service based secondary
        persona = (item.buyer_persona or "").lower()
        secondary = ChannelKind.LINKEDIN
        if "founder" in persona or "ceo" in persona:
            secondary = ChannelKind.LINKEDIN
        elif "cto" in persona or "engineer" in persona:
            secondary = ChannelKind.PERSONALIZED_VIDEO
        elif item.opportunity_score >= 85:
            secondary = ChannelKind.WHATSAPP_BUSINESS
        else:
            secondary = ChannelKind.LINKEDIN

        if primary == secondary:
            for candidate in CHANNEL_RANK_DEFAULT:
                if candidate != primary:
                    secondary = candidate
                    break

        reason = (
            f"Primary {primary.value} chosen from decision outreach hints and verified contact patterns; "
            f"secondary {secondary.value} selected for persona '{item.buyer_persona or 'unknown'}' "
            f"and opportunity score {item.opportunity_score:.1f}. Delivery remains disabled."
        )
        return primary, secondary, reason

    def _priority(self, item: CampaignInput) -> CampaignPriority:
        score = item.opportunity_score
        urgency = item.opportunity_urgency
        if score >= 85 or urgency >= 80:
            return CampaignPriority.CRITICAL
        if score >= 70:
            return CampaignPriority.HIGH
        if score >= 50:
            return CampaignPriority.MEDIUM
        return CampaignPriority.LOW

    def _package_styles(self, package: dict[str, Any]) -> list[str]:
        styles = []
        for variant in package.get("style_variants") or []:
            if isinstance(variant, dict) and variant.get("style"):
                styles.append(str(variant["style"]))
        return styles

    def _step_confidence(self, item: CampaignInput, readiness: float, draft: dict[str, Any]) -> float:
        base = (item.opportunity_score * 0.5) + (readiness * 0.3)
        if draft.get("body") and "Insufficient verified" not in str(draft.get("body")):
            base += 15.0
        return round(min(100.0, base), 2)

    def _step_evidence(self, item: CampaignInput, channel: ChannelKind, draft: dict[str, Any]) -> list[EvidenceItem]:
        rows = [
            EvidenceItem(
                category="channel",
                summary=f"Planned channel {channel.value} (execution not enabled)",
                source="campaign_intelligence",
                confidence=70.0,
            )
        ]
        if draft.get("title"):
            rows.append(
                EvidenceItem(
                    category="message",
                    summary=f"Draft selected: {draft.get('title')}",
                    source="sales_copilot",
                    confidence=75.0,
                )
            )
        for ev in (item.sales_package.get("evidence_chain") or [])[:3]:
            if isinstance(ev, dict) and ev.get("summary"):
                rows.append(
                    EvidenceItem(
                        category=str(ev.get("category") or "evidence"),
                        summary=str(ev.get("summary")),
                        source=str(ev.get("source") or "beacon"),
                        confidence=float(ev.get("confidence") or 60.0),
                        reference_id=str(ev.get("reference_id")) if ev.get("reference_id") else None,
                    )
                )
        return rows

    def _campaign_evidence(
        self, item: CampaignInput, primary: ChannelKind, secondary: ChannelKind | None
    ) -> list[EvidenceItem]:
        rows = [
            EvidenceItem(
                category="opportunity",
                summary=f"Opportunity score {item.opportunity_score:.1f}",
                source="beacon_opportunity",
                confidence=min(100.0, item.opportunity_score),
                reference_id=str(item.opportunity_id),
            )
        ]
        if item.recommended_service:
            rows.append(
                EvidenceItem(
                    category="service",
                    summary=f"Recommended service: {item.recommended_service}",
                    source="beacon_revenue",
                    confidence=75.0,
                )
            )
        if item.business_pain:
            rows.append(
                EvidenceItem(
                    category="pain",
                    summary=item.business_pain,
                    source="beacon_revenue",
                    confidence=75.0,
                )
            )
        rows.append(
            EvidenceItem(
                category="channel",
                summary=f"Primary={primary.value}; secondary={secondary.value if secondary else 'none'}",
                source="campaign_intelligence",
                confidence=80.0,
            )
        )
        decision = item.decision_discovery or {}
        if decision.get("primary_decision_maker"):
            maker = decision["primary_decision_maker"]
            if isinstance(maker, dict) and maker.get("name"):
                rows.append(
                    EvidenceItem(
                        category="decision_maker",
                        summary=f"{maker.get('name')} — {maker.get('role')}",
                        source="beacon_decision",
                        confidence=float(maker.get("confidence") or 70.0),
                    )
                )
        return rows
