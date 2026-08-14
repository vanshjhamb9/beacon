"""Dataset statistics — rates from raw counters."""

from __future__ import annotations

from intelligence_center.models import DatasetStatistics


def compute_dataset_statistics(
    *,
    signals_collected: int,
    duplicates: int = 0,
    spam: int = 0,
    dead_websites: int = 0,
    working_websites: int = 0,
    emails_found: int = 0,
    verified_emails: int = 0,
    generic_emails: int = 0,
    founder_emails: int = 0,
    decision_makers: int = 0,
    revenue_ready: int = 0,
    outreach_ready: int = 0,
) -> DatasetStatistics:
    signals = max(int(signals_collected or 0), 0)
    websites = max(int(dead_websites or 0) + int(working_websites or 0), 0)
    emails = max(int(emails_found or 0), 0)
    companies_with_enrichment = max(int(working_websites or 0), 1)

    # Duplicates never become stored signals, so rate is over everything observed.
    total_observed = signals + max(int(duplicates or 0), 0)
    duplicate_rate = (
        round((duplicates / total_observed) * 100.0, 1) if total_observed else 0.0
    )
    spam_rate = min(round((spam / signals) * 100.0, 1), 100.0) if signals else 0.0
    verification_rate = (
        round((working_websites / websites) * 100.0, 1) if websites else 0.0
    )
    enrichment_coverage = round(
        (
            (1 if emails_found else 0)
            + (1 if decision_makers else 0)
            + (1 if verified_emails else 0)
        )
        / 3.0
        * min(emails / companies_with_enrichment, 1.0)
        * 100.0,
        1,
    ) if working_websites else 0.0

    return DatasetStatistics(
        signals_collected=signals,
        duplicates=int(duplicates or 0),
        spam=int(spam or 0),
        dead_websites=int(dead_websites or 0),
        working_websites=int(working_websites or 0),
        emails_found=emails,
        verified_emails=int(verified_emails or 0),
        generic_emails=int(generic_emails or 0),
        founder_emails=int(founder_emails or 0),
        decision_makers=int(decision_makers or 0),
        revenue_ready=int(revenue_ready or 0),
        outreach_ready=int(outreach_ready or 0),
        duplicate_rate=duplicate_rate,
        spam_rate=spam_rate,
        verification_rate=verification_rate,
        enrichment_coverage=enrichment_coverage,
    )
