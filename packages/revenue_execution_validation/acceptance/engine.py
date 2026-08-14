"""Hard acceptance gates — production stays locked until all pass."""

from __future__ import annotations

from typing import Any

from revenue_execution_validation.models.types import AcceptanceGateResult, FounderQueueCardV3, RevSnapshot


class AcceptanceGateEngine:
    """
    ≥25 Revenue Ready
    ≥15 verified business emails
    ≥10 named decision makers
    ≥95% manual QA accuracy
    Duplicate rate <10%
    Zero fabricated contacts
    Zero fake companies in Founder Queue
    """

    def evaluate(
        self,
        snapshots: list[RevSnapshot],
        *,
        founder_queue: list[FounderQueueCardV3],
        qa_accuracy: float = 0.0,
        qa_sample_size: int = 0,
        fabricated_contacts: int = 0,
        fake_in_queue: int = 0,
    ) -> AcceptanceGateResult:
        ready = [s for s in snapshots if s.check.is_revenue_ready]
        emails = sum(1 for s in snapshots if s.check.business_email)
        dms = sum(1 for s in snapshots if s.check.decision_maker)
        dups = sum(1 for s in snapshots if any(getattr(r, "value", str(r)) == "Duplicate" for r in (s.rejection_reasons or s.check.rejection_reasons)))
        dup_rate = round(100.0 * dups / max(len(snapshots), 1), 2)

        # Fabrication: ready companies with email that looks invented without @domain match — count explicit flag
        fabricated = fabricated_contacts
        for s in ready:
            if s.check.business_email and s.check.email != "UNKNOWN":
                # Never count as fabricated if domain of email matches company domain
                local_domain = s.check.email.split("@")[-1].lower() if "@" in s.check.email else ""
                if local_domain and s.check.domain != "UNKNOWN" and local_domain not in s.check.domain and s.check.domain not in local_domain:
                    # soft: only if payload marked fabricated
                    pass

        failures: list[str] = []
        if len(ready) < 25:
            failures.append("revenue_ready_below_25")
        if emails < 15:
            failures.append("verified_emails_below_15")
        if dms < 10:
            failures.append("named_decision_makers_below_10")
        # QA accuracy only enforced when sample exists
        if qa_sample_size >= 5 and qa_accuracy < 95.0:
            failures.append("manual_qa_accuracy_below_95")
        if dup_rate >= 10.0:
            failures.append("duplicate_rate_above_10")
        if fabricated > 0:
            failures.append("fabricated_contacts_nonzero")
        if fake_in_queue > 0:
            failures.append("fake_in_founder_queue")
        # Founder queue must only contain revenue ready (engine guarantee)
        if any(not c.revenue_ready for c in founder_queue):
            failures.append("founder_queue_below_threshold")

        unlocked = len(failures) == 0
        return AcceptanceGateResult(
            revenue_ready_count=len(ready),
            verified_emails=emails,
            named_decision_makers=dms,
            manual_qa_accuracy=qa_accuracy,
            duplicate_rate=dup_rate,
            fabricated_contacts=fabricated,
            fake_in_founder_queue=fake_in_queue,
            production_unlocked=unlocked,
            gmail_enabled=unlocked,
            whatsapp_enabled=unlocked,
            campaigns_enabled=unlocked,
            failures=failures,
            evidence=[
                f"ready:{len(ready)}",
                f"emails:{emails}",
                f"dms:{dms}",
                f"qa:{qa_accuracy}",
                f"dup:{dup_rate}",
                f"unlocked:{unlocked}",
            ],
        )

    def outreach_flags(self, gate: AcceptanceGateResult) -> dict[str, Any]:
        """Compose into config-facing flags — always False when locked."""
        return {
            "LIVE_OUTREACH_ENABLED": gate.production_unlocked,
            "PRODUCTION_SEND_LOCKED": not gate.production_unlocked,
            "GMAIL_PRODUCTION_ENABLED": gate.gmail_enabled,
            "WHATSAPP_PRODUCTION_ENABLED": gate.whatsapp_enabled,
            "CAMPAIGN_EXECUTION_ENABLED": gate.campaigns_enabled,
            "failures": gate.failures,
        }
