from __future__ import annotations

from live_revenue_execution.models.types import LREInput, WhatsAppPlan


class WhatsAppExecutionEngine:
    """Compose WhatsApp Business plans — founder approval always required."""

    def build(self, item: LREInput) -> WhatsAppPlan | None:
        to_address = item.to_whatsapp or ""
        if not to_address and not item.whatsapp_body:
            # Still produce a preview card when email path exists
            if not item.to_email:
                return None
            to_address = item.to_email
        body = item.whatsapp_body or self._default_body(item)
        buttons: list[dict[str, str]] = []
        if item.calendly_url:
            buttons.append({"type": "url", "text": "Book meeting", "url": item.calendly_url})
            if item.calendly_url not in body:
                body = f"{body}\n\nBook: {item.calendly_url}"
        media = [
            {"kind": a.get("kind") or "document", "filename": a.get("filename"), "url": a.get("url")}
            for a in item.attachments
            if a.get("url") or a.get("content_base64")
        ]
        return WhatsAppPlan(
            to_address=to_address,
            body_text=body,
            template_name=None,
            buttons=buttons,
            media=media,
            calendly_url=item.calendly_url,
            requires_founder_approval=True,
            evidence=[
                "founder_approval_required:true",
                f"buttons:{len(buttons)}",
                f"media:{len(media)}",
                "provider:meta_whatsapp",
            ],
        )

    def _default_body(self, item: LREInput) -> str:
        offer = item.recommended_service or "a short discovery call"
        pain = item.pain_points[0] if item.pain_points else "ops bottlenecks"
        return (
            f"Hi — quick note from Inowix. Noticed {item.company_name} is facing {pain}. "
            f"We can help with {offer}. Reply YES if useful."
        )
