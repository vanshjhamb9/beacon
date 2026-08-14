from __future__ import annotations

from typing import Any

from campaign_intelligence.models.types import ChannelKind
from campaign_intelligence.templates.defaults import STYLE_BY_PERSONA


DRAFT_KIND_BY_CHANNEL: dict[ChannelKind, str] = {
    ChannelKind.EMAIL: "email",
    ChannelKind.LINKEDIN: "linkedin",
    ChannelKind.WHATSAPP_BUSINESS: "whatsapp",
    ChannelKind.PERSONALIZED_VIDEO: "video_script",
    ChannelKind.PHONE_CALL: "discovery_question",
    ChannelKind.CALENDAR_INVITATION: "meeting_agenda",
}

FOLLOW_UP_KINDS = ("follow_up_1", "follow_up_2", "follow_up_3")


class MessageSelector:
    """Select best Sales Copilot draft variant without inventing copy."""

    def preferred_style(
        self,
        *,
        buyer_persona: str | None,
        industry: str | None,
        company_size: str | None,
        recommended_service: str,
        package_styles: list[str],
    ) -> str:
        persona = (buyer_persona or "").strip().lower()
        style = "professional"
        for key, mapped in STYLE_BY_PERSONA.items():
            if key in persona:
                style = mapped
                break
        if company_size and any(token in company_size.lower() for token in ("enterprise", "1000+", "5000")):
            style = "enterprise"
        if industry and "software" in industry.lower() and "cto" in persona:
            style = "technical"
        if recommended_service and "agent" in recommended_service.lower() and style == "professional":
            style = "consultative"
        if package_styles and style not in package_styles:
            style = package_styles[0]
        return style

    def select_draft(
        self,
        *,
        sales_package: dict[str, Any],
        channel: ChannelKind,
        style: str,
        follow_up_index: int | None = None,
    ) -> tuple[dict[str, Any], str]:
        kind = DRAFT_KIND_BY_CHANNEL[channel]
        if follow_up_index is not None:
            kind = FOLLOW_UP_KINDS[min(follow_up_index, len(FOLLOW_UP_KINDS) - 1)]

        drafts = self._flatten_drafts(sales_package)
        candidates = [d for d in drafts if d.get("kind") == kind and d.get("style") == style]
        if not candidates:
            candidates = [d for d in drafts if d.get("kind") == kind]
        if not candidates:
            return (
                {
                    "kind": kind,
                    "style": style,
                    "title": f"{kind} placeholder",
                    "body": "Insufficient verified Sales Copilot draft for this channel.",
                    "subject_lines": [],
                },
                f"No matching Sales Copilot draft for kind={kind}; using insufficient-draft placeholder.",
            )

        chosen = candidates[0]
        reason = (
            f"Selected Sales Copilot draft kind={kind} style={chosen.get('style')} "
            f"for channel={channel.value} based on persona/industry/size/service matching."
        )
        return chosen, reason

    def _flatten_drafts(self, sales_package: dict[str, Any]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for variant in sales_package.get("style_variants") or []:
            if not isinstance(variant, dict):
                continue
            style = variant.get("style")
            for draft in variant.get("drafts") or []:
                if isinstance(draft, dict):
                    row = dict(draft)
                    row.setdefault("style", style)
                    rows.append(row)
        for draft in sales_package.get("drafts") or []:
            if isinstance(draft, dict):
                rows.append(draft)
        return rows
