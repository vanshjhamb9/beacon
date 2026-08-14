from __future__ import annotations

from live_revenue_execution.models.types import LREInput, OutcomeLearningHint, RevenueAnalyticsSnapshot


class OutcomeLearningComposer:
    """Compose improvement hints — never auto-applies production rules."""

    def hints(self, item: LREInput, analytics: RevenueAnalyticsSnapshot) -> list[OutcomeLearningHint]:
        out: list[OutcomeLearningHint] = []
        open_rate = (analytics.opened / analytics.delivered * 100) if analytics.delivered else 0.0
        reply_rate = (analytics.replies / max(analytics.emails, 1)) * 100
        if analytics.emails >= 5 and open_rate < 25:
            out.append(
                OutcomeLearningHint(
                    metric="open_rate",
                    observation=f"Open rate {open_rate:.1f}% below 25%",
                    recommendation="Test shorter subject lines and earlier personalization tokens.",
                    requires_human_approval=True,
                    confidence=72.0,
                    evidence=[f"opened:{analytics.opened}", f"delivered:{analytics.delivered}"],
                )
            )
        if analytics.emails >= 5 and reply_rate < 8:
            out.append(
                OutcomeLearningHint(
                    metric="reply_rate",
                    observation=f"Reply rate {reply_rate:.1f}% below 8%",
                    recommendation="Strengthen pain-first opening and single clear CTA.",
                    requires_human_approval=True,
                    confidence=70.0,
                    evidence=[f"replies:{analytics.replies}", f"emails:{analytics.emails}"],
                )
            )
        if item.industry:
            out.append(
                OutcomeLearningHint(
                    metric="industry_success",
                    observation=f"Track win rate for industry={item.industry}",
                    recommendation="Keep industry-specific case studies attached for this segment.",
                    requires_human_approval=True,
                    confidence=60.0,
                    evidence=[f"industry:{item.industry}", f"service:{item.recommended_service or 'n/a'}"],
                )
            )
        if analytics.lost and not analytics.won:
            out.append(
                OutcomeLearningHint(
                    metric="loss_reason",
                    observation="Losses without wins in current window",
                    recommendation="Capture loss reasons and feed Campaign Intelligence timing rules (approval required).",
                    requires_human_approval=True,
                    confidence=65.0,
                    evidence=[f"lost:{analytics.lost}", f"won:{analytics.won}"],
                )
            )
        return out
