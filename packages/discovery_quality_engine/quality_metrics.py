"""Quality metrics collection and aggregation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class GateMetric:
    gate_name: str
    total_evaluated: int = 0
    total_passed: int = 0
    total_failed: int = 0
    avg_duration_ms: float = 0.0
    last_evaluated_at: datetime | None = None


@dataclass
class ConnectorMetric:
    connector_name: str
    total_signals: int = 0
    accepted: int = 0
    rejected: int = 0
    acceptance_rate: float = 0.0
    avg_trust_score: float = 0.0


@dataclass
class QualityMetrics:
    period_start: datetime = field(default_factory=lambda: datetime.now(UTC))
    period_end: datetime | None = None
    total_signals: int = 0
    total_accepted: int = 0
    total_rejected: int = 0
    total_held: int = 0
    acceptance_rate: float = 0.0
    gate_metrics: dict[str, GateMetric] = field(default_factory=dict)
    connector_metrics: dict[str, ConnectorMetric] = field(default_factory=dict)
    rejection_by_reason: dict[str, int] = field(default_factory=dict)
    rejection_by_gate: dict[str, int] = field(default_factory=dict)
    freshness_avg_age_days: float = 0.0
    freshness_max_age_days: int = 0
    source_trust_avg: float = 0.0
    duplicate_rate: float = 0.0


class QualityMetricsCollector:
    def __init__(self) -> None:
        self._gate_metrics: dict[str, GateMetric] = {}
        self._connector_metrics: dict[str, ConnectorMetric] = {}
        self._rejection_by_reason: dict[str, int] = {}
        self._rejection_by_gate: dict[str, int] = {}
        self._total_signals = 0
        self._total_accepted = 0
        self._total_rejected = 0
        self._total_held = 0
        self._freshness_ages: list[int] = []
        self._trust_scores: list[float] = []
        self._duplicate_count = 0
        self._start = datetime.now(UTC)

    def record_gate_evaluation(
        self,
        gate_name: str,
        passed: bool,
        duration_ms: float = 0.0,
    ) -> None:
        if gate_name not in self._gate_metrics:
            self._gate_metrics[gate_name] = GateMetric(gate_name=gate_name)
        gm = self._gate_metrics[gate_name]
        gm.total_evaluated += 1
        if passed:
            gm.total_passed += 1
        else:
            gm.total_failed += 1
        total = gm.total_evaluated
        gm.avg_duration_ms = (
            (gm.avg_duration_ms * (total - 1) + duration_ms) / total
            if total > 0
            else duration_ms
        )
        gm.last_evaluated_at = datetime.now(UTC)

    def record_connector_signal(
        self,
        connector: str,
        accepted: bool,
        trust_score: float = 0.0,
    ) -> None:
        if connector not in self._connector_metrics:
            self._connector_metrics[connector] = ConnectorMetric(connector_name=connector)
        cm = self._connector_metrics[connector]
        cm.total_signals += 1
        if accepted:
            cm.accepted += 1
        else:
            cm.rejected += 1
        cm.acceptance_rate = cm.accepted / cm.total_signals * 100 if cm.total_signals > 0 else 0.0
        total_trust = cm.avg_trust_score * (cm.total_signals - 1) + trust_score
        cm.avg_trust_score = total_trust / cm.total_signals if cm.total_signals > 0 else 0.0

    def record_decision(
        self,
        decision: str,
        rejection_reasons: list[str] | None = None,
        gates_failed: list[str] | None = None,
        freshness_age_days: int | None = None,
        trust_score: float | None = None,
        is_duplicate: bool = False,
    ) -> None:
        self._total_signals += 1
        if decision == "ACCEPT":
            self._total_accepted += 1
        elif decision == "REJECT":
            self._total_rejected += 1
        elif decision == "HOLD":
            self._total_held += 1

        for reason in (rejection_reasons or []):
            self._rejection_by_reason[reason] = self._rejection_by_reason.get(reason, 0) + 1

        for gate in (gates_failed or []):
            self._rejection_by_gate[gate] = self._rejection_by_gate.get(gate, 0) + 1

        if freshness_age_days is not None:
            self._freshness_ages.append(freshness_age_days)

        if trust_score is not None:
            self._trust_scores.append(trust_score)

        if is_duplicate:
            self._duplicate_count += 1

    def build(self) -> QualityMetrics:
        total = self._total_signals
        return QualityMetrics(
            period_start=self._start,
            period_end=datetime.now(UTC),
            total_signals=total,
            total_accepted=self._total_accepted,
            total_rejected=self._total_rejected,
            total_held=self._total_held,
            acceptance_rate=(self._total_accepted / total * 100) if total > 0 else 0.0,
            gate_metrics=dict(self._gate_metrics),
            connector_metrics=dict(self._connector_metrics),
            rejection_by_reason=dict(self._rejection_by_reason),
            rejection_by_gate=dict(self._rejection_by_gate),
            freshness_avg_age_days=(
                sum(self._freshness_ages) / len(self._freshness_ages)
                if self._freshness_ages
                else 0.0
            ),
            freshness_max_age_days=max(self._freshness_ages) if self._freshness_ages else 0,
            source_trust_avg=(
                sum(self._trust_scores) / len(self._trust_scores)
                if self._trust_scores
                else 0.0
            ),
            duplicate_rate=(self._duplicate_count / total * 100) if total > 0 else 0.0,
        )

    def reset(self) -> None:
        self._gate_metrics.clear()
        self._connector_metrics.clear()
        self._rejection_by_reason.clear()
        self._rejection_by_gate.clear()
        self._total_signals = 0
        self._total_accepted = 0
        self._total_rejected = 0
        self._total_held = 0
        self._freshness_ages.clear()
        self._trust_scores.clear()
        self._duplicate_count = 0
        self._start = datetime.now(UTC)
