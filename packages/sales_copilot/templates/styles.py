from __future__ import annotations

from sales_copilot.models.types import OutreachStyle

STYLE_GUIDANCE: dict[OutreachStyle, dict[str, str]] = {
    OutreachStyle.PROFESSIONAL: {
        "salutation": "Hello",
        "tone": "clear, respectful, and concise",
        "cta": "Would you be open to a brief conversation next week?",
        "signoff": "Best regards",
    },
    OutreachStyle.CONSULTATIVE: {
        "salutation": "Hi",
        "tone": "insight-led and diagnostic",
        "cta": "Happy to share a short diagnostic perspective if useful — open to a 20-minute discussion?",
        "signoff": "Kind regards",
    },
    OutreachStyle.FOUNDER_TO_FOUNDER: {
        "salutation": "Hey",
        "tone": "peer-to-peer and direct",
        "cta": "Curious if this is on your radar — worth a founder-to-founder chat?",
        "signoff": "Cheers",
    },
    OutreachStyle.ENTERPRISE: {
        "salutation": "Dear",
        "tone": "formal, risk-aware, and outcome-focused",
        "cta": "If helpful, I can prepare a concise briefing for your team.",
        "signoff": "Sincerely",
    },
    OutreachStyle.TECHNICAL: {
        "salutation": "Hi",
        "tone": "precise and systems-oriented",
        "cta": "Would a short technical walkthrough be useful for your team?",
        "signoff": "Thanks",
    },
    OutreachStyle.FRIENDLY: {
        "salutation": "Hi",
        "tone": "warm and approachable",
        "cta": "Would love to compare notes for 15 minutes if you're open to it.",
        "signoff": "Thanks so much",
    },
}


def style_label(style: OutreachStyle) -> str:
    return style.value.replace("_", " ").title()
