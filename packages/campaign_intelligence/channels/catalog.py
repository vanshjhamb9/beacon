from __future__ import annotations

from campaign_intelligence.models.types import ChannelCapability, ChannelKind

CHANNEL_CATALOG: dict[ChannelKind, ChannelCapability] = {
    ChannelKind.EMAIL: ChannelCapability(
        kind=ChannelKind.EMAIL,
        label="Email",
        supports_async=True,
        supports_attachments=True,
        requires_opt_in=False,
        max_daily_sends=80,
        min_gap_hours=24.0,
        business_hours_only=True,
        constraints=[
            "Human approval required before any send",
            "No Gmail provider connected in Sprint 14",
            "Prefer verified business email channels only",
        ],
        delivery_ready=False,
    ),
    ChannelKind.WHATSAPP_BUSINESS: ChannelCapability(
        kind=ChannelKind.WHATSAPP_BUSINESS,
        label="WhatsApp Business",
        supports_async=True,
        supports_attachments=False,
        requires_opt_in=True,
        max_daily_sends=30,
        min_gap_hours=48.0,
        business_hours_only=True,
        constraints=[
            "Requires explicit opt-in",
            "No WhatsApp provider connected in Sprint 14",
            "Keep messages short and evidence-grounded",
        ],
        delivery_ready=False,
    ),
    ChannelKind.LINKEDIN: ChannelCapability(
        kind=ChannelKind.LINKEDIN,
        label="LinkedIn",
        supports_async=True,
        supports_attachments=False,
        requires_opt_in=False,
        max_daily_sends=25,
        min_gap_hours=48.0,
        business_hours_only=True,
        constraints=[
            "No LinkedIn API connected in Sprint 14",
            "Use only publicly attributed profiles",
        ],
        delivery_ready=False,
    ),
    ChannelKind.PHONE_CALL: ChannelCapability(
        kind=ChannelKind.PHONE_CALL,
        label="Phone Call",
        supports_async=False,
        supports_attachments=False,
        requires_opt_in=False,
        max_daily_sends=15,
        min_gap_hours=72.0,
        business_hours_only=True,
        constraints=[
            "Manual dial only — no auto-dialer",
            "Use verified business phone numbers only",
        ],
        delivery_ready=False,
    ),
    ChannelKind.PERSONALIZED_VIDEO: ChannelCapability(
        kind=ChannelKind.PERSONALIZED_VIDEO,
        label="Personalized Video",
        supports_async=True,
        supports_attachments=True,
        requires_opt_in=False,
        max_daily_sends=20,
        min_gap_hours=72.0,
        business_hours_only=False,
        constraints=[
            "Script-only in Sprint 14 — no video hosting send",
            "Must reference verified Beacon evidence",
        ],
        delivery_ready=False,
    ),
    ChannelKind.CALENDAR_INVITATION: ChannelCapability(
        kind=ChannelKind.CALENDAR_INVITATION,
        label="Calendar Invitation",
        supports_async=True,
        supports_attachments=False,
        requires_opt_in=False,
        max_daily_sends=20,
        min_gap_hours=24.0,
        business_hours_only=True,
        constraints=[
            "No Calendly/Gmail calendar integration in Sprint 14",
            "Invitation remains draft until Sprint 15 providers",
        ],
        delivery_ready=False,
    ),
}


def get_channel(kind: ChannelKind) -> ChannelCapability:
    return CHANNEL_CATALOG[kind]


def all_channels() -> list[ChannelCapability]:
    return list(CHANNEL_CATALOG.values())
