from __future__ import annotations

from sales_intelligence.models.types import ReplyClass, ReplyIntelligenceResult


REPLY_RULES: list[tuple[ReplyClass, list[str], str]] = [
    (ReplyClass.NEED_MEETING, ["schedule", "call", "meeting", "book", "calendar", "zoom"], "Propose 2–3 concrete meeting slots and include agenda."),
    (ReplyClass.NEED_PROPOSAL, ["proposal", "quote", "pricing", "sow", "scope", "estimate"], "Send a concise proposal outline with budget band and timeline."),
    (ReplyClass.TECHNICAL_QUESTION, ["api", "integration", "architecture", "security review", "how does", "stack"], "Answer with architecture bullets and offer a technical deep-dive."),
    (ReplyClass.BUDGET_CONCERN, ["budget", "expensive", "cost", "price", "afford"], "Reframe with phased scope and ROI; ask for target budget band."),
    (ReplyClass.SECURITY_CONCERN, ["security", "soc2", "compliance", "gdpr", "hipaa", "privacy"], "Share security/compliance pack and offer a security Q&A."),
    (ReplyClass.TIMING_ISSUE, ["next quarter", "later", "not now", "busy", "q3", "q4", "after"], "Acknowledge timing; propose a light discovery to preserve momentum."),
    (ReplyClass.WRONG_CONTACT, ["not the right", "wrong person", "forward", "cc", "talk to"], "Ask for the correct owner and request an intro."),
    (ReplyClass.NOT_INTERESTED, ["not interested", "no thanks", "unsubscribe", "remove", "pass"], "Close politely and leave a single reopen door in 90 days."),
    (ReplyClass.INTERESTED, ["interested", "sounds good", "tell me more", "curious", "yes", "let's"], "Confirm interest, ask one clarifying question, propose next step."),
]


class ReplyIntelligenceEngine:
    def classify(self, reply_text: str, *, subject: str = "") -> ReplyIntelligenceResult:
        text = f"{subject}\n{reply_text}".strip().lower()
        if not text:
            return ReplyIntelligenceResult(
                classification=ReplyClass.UNKNOWN,
                best_response="Ask a short clarifying question and propose a next step.",
                confidence=20.0,
                reason="empty_reply",
                evidence=["empty"],
            )
        best: ReplyIntelligenceResult | None = None
        for cls, patterns, response in REPLY_RULES:
            hits = [p for p in patterns if p in text]
            if not hits:
                continue
            confidence = min(95.0, 55.0 + len(hits) * 12.0)
            candidate = ReplyIntelligenceResult(
                classification=cls,
                best_response=response,
                confidence=round(confidence, 4),
                reason=f"matched:{','.join(hits[:4])}",
                evidence=[f"pattern:{h}" for h in hits[:6]],
            )
            if best is None or candidate.confidence > best.confidence:
                best = candidate
        if best is None:
            return ReplyIntelligenceResult(
                classification=ReplyClass.UNKNOWN,
                best_response="Acknowledge the reply, mirror their language, and ask one discovery question.",
                confidence=40.0,
                reason="no_strong_pattern",
                evidence=["fallback"],
            )
        return best
