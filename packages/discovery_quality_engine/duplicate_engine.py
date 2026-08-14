"""Deterministic duplicate detection engine."""

from __future__ import annotations

from hashlib import sha256
from urllib.parse import urlparse

from discovery_quality_engine.quality_engine import (
    QualityDecision,
    QualityGate,
    RejectionReason,
)


class DuplicateResult:
    __slots__ = ("decision", "reasons", "duplicate_key")

    def __init__(
        self,
        *,
        decision: QualityDecision,
        reasons: tuple[str, ...] = (),
        duplicate_key: str = "",
    ) -> None:
        self.decision = decision
        self.reasons = reasons
        self.duplicate_key = duplicate_key


class DuplicateEngine:
    def __init__(self) -> None:
        self._seen_domains: set[str] = set()
        self._seen_companies: set[str] = set()
        self._seen_opportunities: set[str] = set()
        self._seen_evidence: set[str] = set()
        self._seen_signals: set[str] = set()

    def check_domain(self, domain: str) -> DuplicateResult:
        normalized = self._normalize_domain(domain)
        if normalized in self._seen_domains:
            return DuplicateResult(
                decision=QualityDecision.REJECT,
                reasons=(
                    f"Duplicate domain: {normalized}",
                    RejectionReason.DUPLICATE_DOMAIN.value,
                ),
                duplicate_key=f"domain:{normalized}",
            )
        self._seen_domains.add(normalized)
        return DuplicateResult(
            decision=QualityDecision.ACCEPT,
            reasons=(f"Unique domain: {normalized}",),
            duplicate_key=f"domain:{normalized}",
        )

    def check_company(self, company_name: str) -> DuplicateResult:
        normalized = self._normalize_company(company_name)
        if normalized in self._seen_companies:
            return DuplicateResult(
                decision=QualityDecision.REJECT,
                reasons=(
                    f"Duplicate company: {normalized}",
                    RejectionReason.DUPLICATE_COMPANY.value,
                ),
                duplicate_key=f"company:{normalized}",
            )
        self._seen_companies.add(normalized)
        return DuplicateResult(
            decision=QualityDecision.ACCEPT,
            reasons=(f"Unique company: {normalized}",),
            duplicate_key=f"company:{normalized}",
        )

    def check_opportunity(
        self,
        company_name: str,
        signal_type: str,
        signal_source: str,
    ) -> DuplicateResult:
        key = self._opportunity_key(company_name, signal_type, signal_source)
        if key in self._seen_opportunities:
            return DuplicateResult(
                decision=QualityDecision.REJECT,
                reasons=(
                    f"Duplicate opportunity for {company_name} / {signal_type}",
                    RejectionReason.DUPLICATE_OPPORTUNITY.value,
                ),
                duplicate_key=f"opportunity:{key}",
            )
        self._seen_opportunities.add(key)
        return DuplicateResult(
            decision=QualityDecision.ACCEPT,
            reasons=(f"Unique opportunity: {key}",),
            duplicate_key=f"opportunity:{key}",
        )

    def check_evidence(self, url: str, title: str) -> DuplicateResult:
        key = self._evidence_key(url, title)
        if key in self._seen_evidence:
            return DuplicateResult(
                decision=QualityDecision.REJECT,
                reasons=(
                    f"Duplicate evidence: {title[:50]}",
                    RejectionReason.DUPLICATE_EVIDENCE.value,
                ),
                duplicate_key=f"evidence:{key}",
            )
        self._seen_evidence.add(key)
        return DuplicateResult(
            decision=QualityDecision.ACCEPT,
            reasons=(f"Unique evidence: {title[:50]}",),
            duplicate_key=f"evidence:{key}",
        )

    def check_signal(
        self,
        company_name: str,
        signal_type: str,
    ) -> DuplicateResult:
        key = self._signal_key(company_name, signal_type)
        if key in self._seen_signals:
            return DuplicateResult(
                decision=QualityDecision.REJECT,
                reasons=(
                    f"Duplicate signal: {company_name} / {signal_type}",
                    RejectionReason.DUPLICATE_SIGNAL.value,
                ),
                duplicate_key=f"signal:{key}",
            )
        self._seen_signals.add(key)
        return DuplicateResult(
            decision=QualityDecision.ACCEPT,
            reasons=(f"Unique signal: {key}",),
            duplicate_key=f"signal:{key}",
        )

    def reset(self) -> None:
        self._seen_domains.clear()
        self._seen_companies.clear()
        self._seen_opportunities.clear()
        self._seen_evidence.clear()
        self._seen_signals.clear()

    def gate_name(self) -> str:
        return QualityGate.DUPLICATE_CHECK.value

    def _normalize_domain(self, domain: str) -> str:
        d = domain.lower().strip()
        d = d.removeprefix("http://").removeprefix("https://")
        d = d.removeprefix("www.")
        d = d.split("/")[0].split(":")[0]
        return d

    def _normalize_company(self, name: str) -> str:
        n = name.lower().strip()
        n = n.replace("inc.", " ").replace("inc", " ")
        n = n.replace("llc", " ").replace("ltd.", " ").replace("ltd", " ")
        n = n.replace("corp.", " ").replace("corp", " ").replace("corporation", " ")
        n = n.replace("co.", " ").replace(" co ", " ").replace("company", " ")
        n = n.replace("group", " ").replace("holdings", " ")
        n = " ".join(n.split())
        return n

    def _opportunity_key(self, company: str, signal_type: str, source: str) -> str:
        raw = f"{self._normalize_company(company)}|{signal_type.lower()}|{source.lower()}"
        return sha256(raw.encode()).hexdigest()[:16]

    def _evidence_key(self, url: str, title: str) -> str:
        raw = f"{url.lower().strip()}|{title.lower().strip()}"
        return sha256(raw.encode()).hexdigest()[:16]

    def _signal_key(self, company: str, signal_type: str) -> str:
        raw = f"{self._normalize_company(company)}|{signal_type.lower()}"
        return sha256(raw.encode()).hexdigest()[:16]
