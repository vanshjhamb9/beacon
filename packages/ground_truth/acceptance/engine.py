from __future__ import annotations

from typing import Any

from ground_truth.models.types import GtAcceptance


class GtAcceptanceEngine:
    """Final acceptance — production only when ground-truth KPIs are met."""

    def evaluate(self, metrics: dict[str, Any]) -> GtAcceptance:
        real_companies = int(metrics.get("real_companies") or 0)
        identities = float(metrics.get("real_identities_percent") or 0)
        websites = float(metrics.get("websites_percent") or 0)
        dms = float(metrics.get("decision_makers_percent") or 0)
        contacts = float(metrics.get("verified_contact_percent") or 0)
        dup = float(metrics.get("duplicate_percent") or 100)
        fake = float(metrics.get("fake_percent") or 100)
        evidence = float(metrics.get("evidence_coverage_percent") or 0)
        founder = float(metrics.get("founder_email_confidence_percent") or 0)

        failures: list[str] = []
        if real_companies < 500:
            failures.append("real_companies_below_500")
        if identities < 95:
            failures.append("identities_below_95")
        if websites < 90:
            failures.append("websites_below_90")
        if dms < 80:
            failures.append("decision_makers_below_80")
        if contacts < 70:
            failures.append("verified_contacts_below_70")
        if dup >= 10:
            failures.append("duplicates_above_10")
        if fake >= 2:
            failures.append("fake_above_2")
        if evidence < 100:
            failures.append("evidence_not_universal")
        if founder < 50:
            failures.append("founder_email_confidence_below_50")

        unlocked = len(failures) == 0
        return GtAcceptance(
            real_companies=real_companies,
            real_identities_percent=identities,
            websites_percent=websites,
            decision_makers_percent=dms,
            verified_contact_percent=contacts,
            duplicate_percent=dup,
            fake_percent=fake,
            evidence_coverage_percent=evidence,
            founder_email_confidence_percent=founder,
            production_unlocked=unlocked,
            failures=failures,
            evidence=[f"production_unlocked:{unlocked}", f"failures:{len(failures)}"],
        )
