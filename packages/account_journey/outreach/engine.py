from __future__ import annotations

from account_journey.models.types import AccountJourneyInput, InteractionSignal, OutreachIntelligence


class OutreachIntelligenceEngine:
    def score(self, item: AccountJourneyInput) -> OutreachIntelligence:
        signals: list[InteractionSignal] = []
        if item.emailed:
            signals.append(InteractionSignal(kind="email", weight=8, polarity="neutral", detail="Email sent", evidence=["channel:email"]))
        if item.whatsapp_sent:
            signals.append(InteractionSignal(kind="whatsapp", weight=10, polarity="neutral", detail="WhatsApp sent", evidence=["channel:whatsapp"]))
        if item.meeting_scheduled or item.calendar_booked:
            signals.append(InteractionSignal(kind="meeting", weight=25, polarity="positive", detail="Meeting booked", evidence=["channel:meeting"]))
        if item.replied:
            signals.append(InteractionSignal(kind="reply", weight=30, polarity="positive", detail="Reply received", evidence=["channel:reply"]))
        if item.no_reply_days >= 5 and item.emailed and not item.replied:
            signals.append(InteractionSignal(kind="no_reply", weight=12, polarity="negative", detail=f"No reply {item.no_reply_days}d", evidence=["signal:no_reply"]))
        if item.cta_clicks or item.clicked:
            signals.append(InteractionSignal(kind="cta_clicks", weight=15, polarity="positive", detail=f"CTA clicks:{item.cta_clicks or 1}", evidence=["signal:cta"]))
        if item.video_watched:
            signals.append(InteractionSignal(kind="video_watched", weight=12, polarity="positive", detail="Video watched", evidence=["signal:video"]))
        if item.calendly_opened:
            signals.append(InteractionSignal(kind="calendly_opened", weight=14, polarity="positive", detail="Calendly opened", evidence=["signal:calendly"]))
        if item.calendar_booked:
            signals.append(InteractionSignal(kind="calendar_booked", weight=22, polarity="positive", detail="Calendar booked", evidence=["signal:booked"]))

        positive = sum(s.weight for s in signals if s.polarity == "positive")
        negative = sum(s.weight for s in signals if s.polarity == "negative")
        ghosting = item.no_reply_days >= 8 and item.emailed and not item.replied and not item.opened
        if ghosting:
            signals.append(InteractionSignal(kind="ghosting", weight=18, polarity="negative", detail="Ghosting detected", evidence=["signal:ghosting"]))
            negative += 18
        delta = positive - negative
        return OutreachIntelligence(
            signals=signals,
            positive_score=round(positive, 2),
            negative_score=round(negative, 2),
            ghosting=ghosting,
            account_health_delta=round(delta, 2),
            evidence=[f"pos:{positive}", f"neg:{negative}", f"ghosting:{ghosting}"],
        )
