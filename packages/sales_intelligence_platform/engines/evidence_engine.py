"""Evidence Engine - Compile all evidence records for an account."""

from __future__ import annotations

from datetime import UTC, datetime

from packages.sales_intelligence_platform.models import Account, ContactChannel, DecisionMaker, EvidenceRecord


def compile_evidence(account: Account) -> list[EvidenceRecord]:
    """Compile all evidence records from decision makers, channels, and committee."""
    records: list[EvidenceRecord] = []
    now = datetime.now(UTC).isoformat()

    # Evidence from decision makers
    for dm in account.decision_makers:
        for ev in dm.evidence:
            records.append(EvidenceRecord(
                field_name="decision_maker",
                field_value=f"{dm.name} ({dm.normalized_role})",
                source=dm.source or "website",
                source_url=dm.source_url,
                collector="decision_maker_engine",
                confidence=dm.confidence,
                verification_status="VERIFIED" if dm.confidence >= 0.8 else "UNVERIFIED",
                collected_at=now,
            ))

    # Evidence from contact channels
    for ch in account.contact_channels:
        for ev in ch.evidence:
            records.append(EvidenceRecord(
                field_name="contact_channel",
                field_value=f"{ch.kind}: {ch.value}",
                source=ch.source or "website",
                source_url=ch.source_url,
                collector="contact_discovery",
                confidence=ch.confidence,
                verification_status=ch.verification_level,
                collected_at=now,
            ))

    # Evidence from buying committee
    for ev in account.buying_committee.evidence:
        records.append(EvidenceRecord(
            field_name="buying_committee",
            field_value=ev,
            source="buying_committee_engine",
            collector="buying_committee",
            confidence=account.buying_committee.confidence,
            verification_status="UNVERIFIED",
            collected_at=now,
        ))

    return records
