from __future__ import annotations

from typing import Any

from beacon_alpha.models.types import AlphaAcceptance


class AlphaAcceptanceEngine:
    """Rule 10 — live outreach only when dataset quality thresholds are met."""

    def evaluate(self, metrics: dict[str, Any]) -> AlphaAcceptance:
        real = float(metrics.get("real_business_percent") or 0)
        website = float(metrics.get("working_website_percent") or metrics.get("website_percent") or 0)
        email = float(metrics.get("attributed_email_percent") or metrics.get("email_percent") or 0)
        phone = float(metrics.get("business_phone_percent") or metrics.get("phone_percent") or 0)
        service = float(metrics.get("service_correct_percent") or 0)
        dup = float(metrics.get("duplicate_rate") or metrics.get("duplicate_percent") or 100)
        sales_ready = int(metrics.get("sales_ready_per_day") or metrics.get("sales_ready_today") or 0)
        review_fast = bool(metrics.get("review_under_15_min") or metrics.get("founder_queue_reviewable"))

        failures: list[str] = []
        if real < 95:
            failures.append("real_business_below_95")
        if website < 90:
            failures.append("website_below_90")
        if email < 70:
            failures.append("email_below_70")
        if phone < 40:
            failures.append("phone_below_40")
        if service < 90:
            failures.append("service_correct_below_90")
        if dup >= 5:
            failures.append("duplicate_rate_above_5")
        if sales_ready < 50:
            failures.append("sales_ready_per_day_below_50")
        if not review_fast:
            failures.append("founder_queue_not_reviewable_in_15_min")

        ready = len(failures) == 0
        return AlphaAcceptance(
            real_business_percent=real,
            working_website_percent=website,
            attributed_email_percent=email,
            business_phone_percent=phone,
            service_correct_percent=service,
            duplicate_rate=dup,
            sales_ready_per_day=sales_ready,
            review_under_15_min=review_fast,
            live_outreach_ready=ready,
            failures=failures,
            evidence=[
                f"live_outreach_ready:{ready}",
                f"failures:{len(failures)}",
                "gmail_whatsapp_locked" if not ready else "gmail_whatsapp_unlock_candidate",
            ],
        )
