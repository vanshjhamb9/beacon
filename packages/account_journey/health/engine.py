from __future__ import annotations

from account_journey.models.types import AccountHealth, AccountHealthCategory, AccountJourneyInput, EngagementScores, JourneyStage


class AccountHealthEngine:
    def classify(self, item: AccountJourneyInput, *, stage: JourneyStage, engagement: EngagementScores) -> AccountHealth:
        score = engagement.overall_engagement
        if stage == JourneyStage.DORMANT or item.dormant_days >= 20:
            return AccountHealth(
                category=AccountHealthCategory.DORMANT,
                score=round(score, 2),
                reason="Inactive / dormant account",
                evidence=["health:dormant"],
            )
        if stage == JourneyStage.REACTIVATED:
            return AccountHealth(
                category=AccountHealthCategory.RECOVERED,
                score=round(max(score, 45.0), 2),
                reason="Reactivated after dormancy",
                evidence=["health:recovered"],
            )
        if item.negotiation or item.proposal_requested or (item.replied and engagement.intent_score >= 75):
            return AccountHealth(
                category=AccountHealthCategory.CRITICAL,
                score=round(max(score, 80.0), 2),
                reason="Critical path — founder attention",
                evidence=["health:critical"],
            )
        if engagement.account_temperature >= 75 or engagement.intent_score >= 70:
            return AccountHealth(
                category=AccountHealthCategory.HOT,
                score=round(score, 2),
                reason="Hot engagement",
                evidence=["health:hot"],
            )
        if item.meeting_scheduled or score >= 70:
            return AccountHealth(
                category=AccountHealthCategory.PRIORITY,
                score=round(score, 2),
                reason="Priority account",
                evidence=["health:priority"],
            )
        if score >= 35 or item.opened or item.clicked:
            return AccountHealth(
                category=AccountHealthCategory.WARM,
                score=round(score, 2),
                reason="Warm engagement",
                evidence=["health:warm"],
            )
        return AccountHealth(
            category=AccountHealthCategory.COLD,
            score=round(score, 2),
            reason="Cold / early stage",
            evidence=["health:cold"],
        )
