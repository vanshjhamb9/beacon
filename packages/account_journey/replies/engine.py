from __future__ import annotations

from account_journey.models.types import AccountJourneyInput, ReplyClass, ReplyClassification


PATTERNS: list[tuple[ReplyClass, list[str], float]] = [
    (ReplyClass.MEETING_REQUESTED, ["meet", "call", "schedule", "calendly", "book time"], 92.0),
    (ReplyClass.NEED_PROPOSAL, ["proposal", "quote", "sow", "pricing pack", "send pricing"], 90.0),
    (ReplyClass.BUDGET_CONCERN, ["budget", "expensive", "cost", "price", "afford"], 88.0),
    (ReplyClass.NOT_NOW, ["not now", "not interested right now", "revisit later", "pause for now"], 89.0),
    (ReplyClass.TIMING_CONCERN, ["timing", "next quarter", "not this month", "too busy"], 86.0),
    (ReplyClass.COMPETITOR, ["already using", "vendor", "incumbent", "competitor"], 85.0),
    (ReplyClass.WRONG_CONTACT, ["wrong person", "not the right", "forward to", "misdirected"], 87.0),
    (ReplyClass.SPAM, ["unsubscribe", "spam", "stop emailing", "remove me"], 95.0),
    (ReplyClass.INTERESTED, ["interested", "sounds good", "tell me more", "curious", "yes"], 80.0),
]


class ReplyIntelligenceV2Engine:
    def classify(self, item: AccountJourneyInput) -> ReplyClassification | None:
        if not item.replied and not item.reply_text.strip():
            return None
        text = (item.reply_text or "").lower()
        if not text and item.replied:
            text = "interested tell me more"
        best: ReplyClassification | None = None
        for cls, patterns, conf in PATTERNS:
            hits = [p for p in patterns if p in text]
            if not hits:
                continue
            candidate = ReplyClassification(
                classification=cls,
                confidence=min(99.0, conf + len(hits) * 2.0),
                structured_outcome={
                    "label": cls.value,
                    "hits": hits[:4],
                    "company_name": item.company_name,
                    "next_hint": self._hint(cls),
                },
                evidence=[f"hits:{','.join(hits[:4])}", f"class:{cls.value}"],
            )
            if best is None or candidate.confidence > best.confidence:
                best = candidate
        return best or ReplyClassification(
            classification=ReplyClass.UNKNOWN,
            confidence=40.0,
            structured_outcome={"label": "unknown", "company_name": item.company_name},
            evidence=["class:unknown"],
        )

    def _hint(self, cls: ReplyClass) -> str:
        return {
            ReplyClass.INTERESTED: "Book discovery meeting",
            ReplyClass.NEED_PROPOSAL: "Prepare proposal",
            ReplyClass.BUDGET_CONCERN: "Share phased pricing",
            ReplyClass.TIMING_CONCERN: "Schedule nurture touch",
            ReplyClass.NOT_NOW: "Park with reminder",
            ReplyClass.COMPETITOR: "Differentiate vs incumbent",
            ReplyClass.WRONG_CONTACT: "Ask for referral",
            ReplyClass.SPAM: "Stop sequence",
            ReplyClass.MEETING_REQUESTED: "Send Calendly / confirm slot",
            ReplyClass.UNKNOWN: "Manual review",
        }[cls]
