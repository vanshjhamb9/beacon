from __future__ import annotations

from campaign_intelligence.models.types import ChannelKind, ScheduleRules

DEFAULT_SEQUENCE_DELAYS = [0.0, 48.0, 96.0, 168.0]

STYLE_BY_PERSONA: dict[str, str] = {
    "founder": "founder_to_founder",
    "ceo": "founder_to_founder",
    "cto": "technical",
    "head of engineering": "technical",
    "engineering manager": "technical",
    "coo": "consultative",
    "operations": "consultative",
    "sales": "professional",
    "marketing": "friendly",
    "enterprise": "enterprise",
}

CHANNEL_RANK_DEFAULT = [
    ChannelKind.EMAIL,
    ChannelKind.LINKEDIN,
    ChannelKind.WHATSAPP_BUSINESS,
    ChannelKind.PERSONALIZED_VIDEO,
    ChannelKind.PHONE_CALL,
    ChannelKind.CALENDAR_INVITATION,
]


def default_schedule(*, timezone: str = "UTC") -> ScheduleRules:
    return ScheduleRules(timezone=timezone or "UTC", sequence_delay_hours=list(DEFAULT_SEQUENCE_DELAYS))
