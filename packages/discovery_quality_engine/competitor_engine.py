"""Deterministic competitor filter — reject known competitors, partners, clients, demo/test companies."""

from __future__ import annotations

from pathlib import Path

import yaml

from discovery_quality_engine.quality_engine import (
    QualityDecision,
    QualityGate,
    RejectionReason,
)


class CompetitorConfig:
    __slots__ = ("competitors", "partners", "existing_clients", "internal_test", "demo_companies")

    def __init__(
        self,
        *,
        competitors: list[str] | None = None,
        partners: list[str] | None = None,
        existing_clients: list[str] | None = None,
        internal_test: list[str] | None = None,
        demo_companies: list[str] | None = None,
    ) -> None:
        self.competitors = [c.lower().strip() for c in (competitors or [])]
        self.partners = [p.lower().strip() for p in (partners or [])]
        self.existing_clients = [c.lower().strip() for c in (existing_clients or [])]
        self.internal_test = [t.lower().strip() for t in (internal_test or [])]
        self.demo_companies = [d.lower().strip() for d in (demo_companies or [])]

    @classmethod
    def from_yaml(cls, path: str | Path) -> "CompetitorConfig":
        p = Path(path)
        if not p.exists():
            return cls()
        with p.open() as f:
            data = yaml.safe_load(f) or {}
        return cls(
            competitors=data.get("competitors", []),
            partners=data.get("partners", []),
            existing_clients=data.get("existing_clients", []),
            internal_test=data.get("internal_test", []),
            demo_companies=data.get("demo_companies", []),
        )

    def all_blocked(self) -> list[str]:
        return (
            self.competitors
            + self.partners
            + self.existing_clients
            + self.internal_test
            + self.demo_companies
        )


class CompetitorResult:
    __slots__ = ("decision", "reasons", "category")

    def __init__(
        self,
        *,
        decision: QualityDecision,
        reasons: tuple[str, ...] = (),
        category: str = "",
    ) -> None:
        self.decision = decision
        self.reasons = reasons
        self.category = category


class CompetitorEngine:
    def __init__(self, config: CompetitorConfig | None = None) -> None:
        self._config = config or CompetitorConfig()

    def evaluate(self, company_name: str) -> CompetitorResult:
        normalized = company_name.lower().strip()

        if not normalized:
            return CompetitorResult(
                decision=QualityDecision.REJECT,
                reasons=(
                    "Empty company name",
                    RejectionReason.UNKNOWN.value,
                ),
                category="invalid",
            )

        for name in self._config.competitors:
            if self._matches(normalized, name):
                return CompetitorResult(
                    decision=QualityDecision.REJECT,
                    reasons=(
                        f"Competitor detected: {name}",
                        RejectionReason.COMPETITOR.value,
                    ),
                    category="competitor",
                )

        for name in self._config.existing_clients:
            if self._matches(normalized, name):
                return CompetitorResult(
                    decision=QualityDecision.REJECT,
                    reasons=(
                        f"Existing client: {name}",
                        RejectionReason.EXISTING_CLIENT.value,
                    ),
                    category="existing_client",
                )

        for name in self._config.demo_companies:
            if self._matches(normalized, name):
                return CompetitorResult(
                    decision=QualityDecision.REJECT,
                    reasons=(
                        f"Demo company: {name}",
                        RejectionReason.DEMO_COMPANY.value,
                    ),
                    category="demo_company",
                )

        for name in self._config.internal_test:
            if self._matches(normalized, name):
                return CompetitorResult(
                    decision=QualityDecision.REJECT,
                    reasons=(
                        f"Internal test company: {name}",
                        RejectionReason.DEMO_COMPANY.value,
                    ),
                    category="internal_test",
                )

        return CompetitorResult(
            decision=QualityDecision.ACCEPT,
            reasons=("Not a competitor, client, or demo company",),
        )

    def gate_name(self) -> str:
        return QualityGate.COMPETITOR_CHECK.value

    def _matches(self, name: str, blocked: str) -> bool:
        return name == blocked or blocked in name or name in blocked
