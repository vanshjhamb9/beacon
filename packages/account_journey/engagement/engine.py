from __future__ import annotations

from account_journey.models.types import AccountJourneyInput, EngagementScores, OutreachIntelligence


class EngagementScoringEngine:
    def score(self, item: AccountJourneyInput, *, outreach: OutreachIntelligence) -> EngagementScores:
        open_score = min(100.0, (40.0 if item.opened else 0.0) + (item.cta_clicks * 8.0) + (15.0 if item.video_watched else 0.0))
        reply_score = min(100.0, (70.0 if item.replied else 0.0) + (20.0 if item.no_reply_days == 0 and item.emailed else 0.0))
        if item.no_reply_days >= 5 and not item.replied:
            reply_score = max(0.0, reply_score - item.no_reply_days * 2.0)
        intent_score = min(100.0, float(item.buying_intent) * 0.7 + float(item.probability) * 0.3 + (15.0 if item.calendly_opened else 0.0))
        meeting_score = min(
            100.0,
            (80.0 if item.meeting_scheduled or item.calendar_booked else 0.0)
            + (25.0 if item.calendly_opened else 0.0)
            + (10.0 if item.proposal_requested else 0.0),
        )
        relationship = min(
            100.0,
            (len(item.decision_makers) * 12.0)
            + (20.0 if item.replied else 0.0)
            + (25.0 if item.meeting_scheduled else 0.0)
            + (15.0 if item.founder_notes else 0.0)
            + outreach.account_health_delta * 0.2,
        )
        temperature = min(100.0, max(0.0, (open_score * 0.15 + reply_score * 0.25 + intent_score * 0.25 + meeting_score * 0.2 + relationship * 0.15)))
        overall = min(100.0, max(0.0, (open_score + reply_score + intent_score + meeting_score + relationship) / 5.0))
        return EngagementScores(
            open_score=round(open_score, 2),
            reply_score=round(max(0.0, reply_score), 2),
            intent_score=round(max(0.0, intent_score), 2),
            meeting_score=round(max(0.0, meeting_score), 2),
            relationship_score=round(max(0.0, relationship), 2),
            account_temperature=round(temperature, 2),
            overall_engagement=round(overall, 2),
            evidence=[f"open:{open_score}", f"reply:{reply_score}", f"intent:{intent_score}", f"temp:{temperature}"],
        )
