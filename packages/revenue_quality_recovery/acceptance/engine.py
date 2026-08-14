from __future__ import annotations

from typing import Any

from revenue_quality_recovery.models.types import AcceptanceCriteria


class AcceptanceEngine:
    """Rule 12 — production send stays locked until acceptance criteria pass."""

    THRESHOLDS = {
        "identity_percent": 95.0,
        "website_percent": 90.0,
        "verified_email_percent": 70.0,
        "phone_or_alt_percent": 50.0,
        "duplicate_rate_max": 10.0,
        "fake_percent_max": 1.0,
        "evidence_attribution_percent": 100.0,
        "outreach_ready_min": 50,
        "manual_review_sample_min": 100,
        "manual_review_accuracy_min": 95.0,
    }

    def evaluate(self, metrics: dict[str, Any]) -> AcceptanceCriteria:
        identity = float(metrics.get("identity_percent") or 0)
        website = float(metrics.get("website_percent") or 0)
        email = float(metrics.get("verified_email_percent") or metrics.get("contacts_percent") or 0)
        phone_alt = float(metrics.get("phone_or_alt_percent") or metrics.get("phone_percent") or 0)
        dup = float(metrics.get("duplicate_rate") or metrics.get("duplicate_percent") or 100)
        fake = float(metrics.get("fake_percent") or 100)
        evidence = float(metrics.get("evidence_attribution_percent") or 0)
        founder_only = bool(metrics.get("founder_queue_sales_ready_only"))
        outreach = int(metrics.get("outreach_ready_count") or metrics.get("sales_ready_count") or 0)
        sample = int(metrics.get("manual_review_sample") or 0)
        accuracy = float(metrics.get("manual_review_accuracy") or 0)

        failures: list[str] = []
        if identity < self.THRESHOLDS["identity_percent"]:
            failures.append("identity_below_95")
        if website < self.THRESHOLDS["website_percent"]:
            failures.append("website_below_90")
        if email < self.THRESHOLDS["verified_email_percent"]:
            failures.append("email_below_70")
        if phone_alt < self.THRESHOLDS["phone_or_alt_percent"]:
            failures.append("phone_or_alt_below_50")
        if dup >= self.THRESHOLDS["duplicate_rate_max"]:
            failures.append("duplicate_rate_above_10")
        if fake >= self.THRESHOLDS["fake_percent_max"]:
            failures.append("fake_above_1")
        if evidence < self.THRESHOLDS["evidence_attribution_percent"]:
            failures.append("evidence_attribution_incomplete")
        if not founder_only:
            failures.append("founder_queue_not_sales_ready_only")
        if outreach < self.THRESHOLDS["outreach_ready_min"]:
            failures.append("outreach_ready_below_50")
        if sample < self.THRESHOLDS["manual_review_sample_min"]:
            failures.append("manual_review_sample_below_100")
        if accuracy < self.THRESHOLDS["manual_review_accuracy_min"]:
            failures.append("manual_review_accuracy_below_95")

        unlocked = len(failures) == 0
        return AcceptanceCriteria(
            identity_percent=identity,
            website_percent=website,
            verified_email_percent=email,
            phone_or_alt_percent=phone_alt,
            duplicate_rate=dup,
            fake_percent=fake,
            evidence_attribution_percent=evidence,
            founder_queue_sales_ready_only=founder_only,
            outreach_ready_count=outreach,
            manual_review_sample=sample,
            manual_review_accuracy=accuracy,
            production_unlocked=unlocked,
            failures=failures,
            evidence=[
                f"production_unlocked:{unlocked}",
                f"failures:{len(failures)}",
                "production_send_disabled" if not unlocked else "production_send_enabled",
            ],
        )
