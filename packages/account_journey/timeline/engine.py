from __future__ import annotations

from datetime import UTC, datetime

from account_journey.models.types import AccountJourneyInput, TimelineEvent


class AccountTimelineEngine:
    def build(self, item: AccountJourneyInput) -> list[TimelineEvent]:
        now = item.now or datetime.now(UTC)
        events: list[TimelineEvent] = [
            TimelineEvent(event_type="discovery", title="Account discovered", detail=item.company_name, occurred_at=now, evidence=["source:discovery"]),
            TimelineEvent(event_type="research", title="Research", detail=item.industry or "Research signals", occurred_at=now, evidence=["stage:research"]),
        ]
        if item.has_decision_makers or item.decision_makers:
            events.append(
                TimelineEvent(
                    event_type="decision_makers",
                    title="Decision makers found",
                    detail=f"{len(item.decision_makers)} contacts",
                    occurred_at=now,
                    evidence=["stage:dms"],
                )
            )
        if item.emailed:
            events.append(TimelineEvent(event_type="email", title="Email sent", occurred_at=now, evidence=["channel:email"]))
        if item.whatsapp_sent:
            events.append(TimelineEvent(event_type="whatsapp", title="WhatsApp sent", occurred_at=now, evidence=["channel:whatsapp"]))
        if item.replied:
            events.append(TimelineEvent(event_type="reply", title="Reply received", detail=item.reply_text[:200], occurred_at=now, evidence=["channel:reply"]))
        if item.meeting_scheduled or item.calendar_booked:
            events.append(TimelineEvent(event_type="meeting", title="Meeting scheduled", occurred_at=now, evidence=["channel:meeting"]))
        for note in item.founder_notes:
            events.append(
                TimelineEvent(
                    event_type="founder_note",
                    title="Founder note",
                    detail=note[:400],
                    occurred_at=now,
                    actor="founder",
                    evidence=["actor:founder"],
                )
            )
        if item.campaign_active or item.campaign_name:
            events.append(
                TimelineEvent(
                    event_type="campaign_change",
                    title="Campaign update",
                    detail=item.campaign_name or "Campaign active",
                    occurred_at=now,
                    evidence=["channel:campaign"],
                )
            )
        events.append(
            TimelineEvent(
                event_type="forecast_update",
                title="Forecast update",
                detail=f"Probability {item.probability} · Intent {item.buying_intent}",
                occurred_at=now,
                evidence=["signal:forecast"],
            )
        )
        for seed in item.timeline_seeds:
            events.append(
                TimelineEvent(
                    event_type=str(seed.get("event_type") or "activity"),
                    title=str(seed.get("title") or "Activity"),
                    detail=str(seed.get("detail") or ""),
                    occurred_at=now,
                    actor=str(seed.get("actor") or "system"),
                    evidence=["seed:true"],
                )
            )
        return events
