"""Reply classification for COMAI partner outreach."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ReplyClassification:
    label: str
    confidence: float
    stage: str
    stop_sequence: bool
    delay_days: int = 0
    evidence: str = ""


RULES: list[tuple[str, list[str], float, str, bool, int]] = [
    ("bounce", ["mailer-daemon", "delivery status notification", "undeliverable", "mailbox unavailable"], 95.0, "bounced", True, 0),
    ("unsubscribe", ["unsubscribe", "remove me", "stop emailing", "opt out", "opt-out"], 92.0, "unsubscribed", True, 0),
    ("ooo", ["out of office", "away from office", "on leave", "automatic reply", "auto-reply"], 90.0, "sent", False, 5),
    ("wrong_person", ["wrong person", "no longer with", "not the right person", "forward this"], 88.0, "nurture", True, 0),
    ("meeting", ["book a call", "schedule", "calendly", "let's meet", "lets meet", "available tomorrow", "zoom"], 86.0, "meeting", True, 0),
    ("interested", ["interested", "tell me more", "sounds good", "send details", "want to know more", "partnership", "demo"], 84.0, "interested", True, 0),
    ("ask_pricing", ["pricing", "commission", "how much", "commercials", "margin"], 83.0, "interested", True, 0),
    ("not_now", ["not now", "next quarter", "revisit later", "busy right now", "circle back"], 82.0, "nurture", True, 0),
    ("not_interested", ["not interested", "no thanks", "pass on this", "don't contact", "do not contact"], 90.0, "lost", True, 0),
]


def classify_reply(text: str) -> ReplyClassification:
    low = (text or "").lower()
    if not low.strip():
        return ReplyClassification("unknown", 0.0, "replied", True, evidence="empty")
    for label, needles, conf, stage, stop, delay in RULES:
        for n in needles:
            if n in low:
                return ReplyClassification(
                    label=label,
                    confidence=conf,
                    stage=stage,
                    stop_sequence=stop,
                    delay_days=delay,
                    evidence=n,
                )
    return ReplyClassification(
        label="replied",
        confidence=60.0,
        stage="replied",
        stop_sequence=True,
        evidence="generic_reply",
    )
