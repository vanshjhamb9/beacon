from __future__ import annotations

import hashlib
import html
import re
from uuid import uuid4

from live_revenue_execution.models.types import LREInput, ProductionEmailPlan


class ProductionEmailEngine:
    """Compose production-ready email content (HTML, tracking, unsubscribe, calendly)."""

    def build(self, item: LREInput) -> ProductionEmailPlan:
        tracking_id = hashlib.sha256(
            f"{item.company_id}:{item.campaign_id}:{item.email_subject or ''}".encode()
        ).hexdigest()[:24]
        subject = item.email_subject or f"Quick idea for {item.company_name}"
        body_text = item.email_body or self._default_text(item)
        calendly = item.calendly_url
        if calendly and calendly not in body_text:
            body_text = f"{body_text.rstrip()}\n\nBook a time: {calendly}"
        unsubscribe_url = f"{item.unsubscribe_base_url.rstrip('/')}/{tracking_id}"
        open_pixel = f"{item.tracking_base_url.rstrip('/')}/o/{tracking_id}.gif"
        body_html = self._to_html(body_text, open_pixel=open_pixel, unsubscribe_url=unsubscribe_url, calendly=calendly)
        evidence = [
            f"tracking_id:{tracking_id}",
            f"subject_len:{len(subject)}",
            f"attachments:{len(item.attachments)}",
            f"calendly:{bool(calendly)}",
            "html:true",
            "unsubscribe:true",
            "open_pixel:true",
        ]
        return ProductionEmailPlan(
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            from_address=item.from_email,
            to_address=item.to_email or "",
            attachments=list(item.attachments),
            calendly_url=calendly,
            tracking_id=tracking_id,
            unsubscribe_url=unsubscribe_url,
            open_pixel_url=open_pixel,
            evidence=evidence,
        )

    def _default_text(self, item: LREInput) -> str:
        pains = ", ".join(item.pain_points[:2]) or "growth bottlenecks"
        offer = item.recommended_service or "a focused engagement"
        dm = ""
        if item.decision_makers:
            name = str(item.decision_makers[0].get("name") or "").strip()
            if name:
                dm = f"Hi {name.split()[0]},\n\n"
        return (
            f"{dm}Noticed {item.company_name} is dealing with {pains}. "
            f"We help similar teams with {offer}. "
            "Happy to share a short case study if useful."
        )

    def _to_html(
        self,
        body_text: str,
        *,
        open_pixel: str,
        unsubscribe_url: str,
        calendly: str | None,
    ) -> str:
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body_text.strip()) if p.strip()]
        blocks = "".join(f"<p style='margin:0 0 14px;line-height:1.5'>{html.escape(p).replace(chr(10), '<br/>')}</p>" for p in paragraphs)
        cta = ""
        if calendly:
            cta = (
                f"<p style='margin:18px 0'><a href='{html.escape(calendly)}' "
                f"style='display:inline-block;padding:10px 16px;background:#0f172a;color:#fff;"
                f"text-decoration:none;border-radius:8px'>Book a meeting</a></p>"
            )
        return (
            "<!DOCTYPE html><html><body style='font-family:Georgia,serif;color:#0f172a;padding:24px'>"
            f"{blocks}{cta}"
            f"<p style='margin-top:28px;font-size:12px;color:#64748b'>"
            f"<a href='{html.escape(unsubscribe_url)}'>Unsubscribe</a></p>"
            f"<img src='{html.escape(open_pixel)}' width='1' height='1' alt='' style='display:none'/>"
            "</body></html>"
        )


class ClickTracker:
    def wrap_links(self, html_body: str, *, tracking_id: str, base_url: str) -> str:
        def repl(match: re.Match[str]) -> str:
            url = match.group(1)
            if "/t/c/" in url or url.endswith(".gif"):
                return match.group(0)
            tracked = f"{base_url.rstrip('/')}/c/{tracking_id}?u={html.escape(url)}"
            return f'href="{tracked}"'

        return re.sub(r'href="([^"]+)"', repl, html_body)
