"""DSIP: Source Reliability Engine.

Every source receives a dynamic trust score.
Confidence of extracted data inherits source reliability.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SourceMetrics:
    """Metrics for a source over a time period."""
    source_id: str
    period_start: datetime = field(default_factory=datetime.utcnow)
    period_end: datetime | None = None

    # Request Metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    timeout_requests: int = 0

    # Extraction Metrics
    total_extracted: int = 0
    verified_extracted: int = 0
    conflicted_extracted: int = 0
    fabricated_detected: int = 0

    # Quality Metrics
    avg_confidence: float = 0.0
    avg_latency_ms: float = 0.0


@dataclass
class ReliabilityScore:
    """Composite reliability score for a source."""
    source_id: str
    accuracy_score: float = 50.0  # 0-100
    coverage_score: float = 50.0
    freshness_score: float = 50.0
    latency_score: float = 50.0
    reliability_score: float = 50.0  # Composite
    calculated_at: datetime = field(default_factory=datetime.utcnow)


class SourceReliabilityEngine:
    """Tracks and calculates dynamic trust scores for every source.

    Metrics tracked:
    - Accuracy: How often extracted data is correct
    - Coverage: How much of the target market is covered
    - Freshness: How recently data was updated
    - Latency: Response time
    - Reliability: Composite score

    Usage:
        engine = SourceReliabilityEngine()
        score = engine.calculate_reliability(source_id, metrics)
        adjusted_confidence = engine.adjust_confidence(source_id, raw_confidence)
    """

    def __init__(self):
        self._metrics: dict[str, list[SourceMetrics]] = {}
        self._scores: dict[str, ReliabilityScore] = {}
        self._history: dict[str, list[dict]] = {}

    def record_request(
        self,
        source_id: str,
        success: bool,
        latency_ms: float = 0.0,
        companies_extracted: int = 0,
    ) -> None:
        """Record a request to a source."""
        metrics = self._get_or_create_metrics(source_id)
        metrics.total_requests += 1

        if success:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1

        if latency_ms > 10000:  # > 10s = timeout
            metrics.timeout_requests += 1

        metrics.total_extracted += companies_extracted

        # Update latency (EMA)
        if latency_ms > 0:
            metrics.avg_latency_ms = metrics.avg_latency_ms * 0.9 + latency_ms * 0.1

    def record_verification(
        self,
        source_id: str,
        verified: bool,
        conflicted: bool = False,
        fabricated: bool = False,
        confidence: float = 0.0,
    ) -> None:
        """Record verification results for extracted data."""
        metrics = self._get_or_create_metrics(source_id)

        if verified:
            metrics.verified_extracted += 1
        if conflicted:
            metrics.conflicted_extracted += 1
        if fabricated:
            metrics.fabricated_detected += 1

        # Update confidence (EMA)
        metrics.avg_confidence = metrics.avg_confidence * 0.9 + confidence * 0.1

    def calculate_reliability(self, source_id: str) -> ReliabilityScore:
        """Calculate composite reliability score for a source."""
        metrics = self._get_or_create_metrics(source_id)

        # Calculate individual scores
        accuracy = self._calculate_accuracy(metrics)
        coverage = self._calculate_coverage(metrics)
        freshness = self._calculate_freshness(source_id)
        latency = self._calculate_latency(metrics)

        # Composite score (weighted average)
        reliability = (
            accuracy * 0.40 +
            coverage * 0.20 +
            freshness * 0.20 +
            latency * 0.20
        )

        score = ReliabilityScore(
            source_id=source_id,
            accuracy_score=accuracy,
            coverage_score=coverage,
            freshness_score=freshness,
            latency_score=latency,
            reliability_score=reliability,
        )

        self._scores[source_id] = score

        # Record in history
        self._history.setdefault(source_id, []).append({
            "date": datetime.utcnow().isoformat(),
            "score": reliability,
            "accuracy": accuracy,
            "coverage": coverage,
            "freshness": freshness,
            "latency": latency,
        })

        return score

    def adjust_confidence(self, source_id: str, raw_confidence: float) -> float:
        """Adjust a confidence score based on source reliability."""
        score = self._scores.get(source_id)
        if not score:
            score = self.calculate_reliability(source_id)

        # Adjust confidence by reliability
        reliability_factor = score.reliability_score / 100
        adjusted = raw_confidence * reliability_factor

        return min(1.0, max(0.0, adjusted))

    def get_reliability_history(self, source_id: str, limit: int = 30) -> list[dict]:
        """Get reliability score history for a source."""
        history = self._history.get(source_id, [])
        return history[-limit:]

    def get_source_rankings(self) -> list[dict]:
        """Get all sources ranked by reliability."""
        rankings = []
        for source_id in self._scores:
            score = self._scores[source_id]
            rankings.append({
                "source_id": source_id,
                "reliability_score": score.reliability_score,
                "accuracy": score.accuracy_score,
                "coverage": score.coverage_score,
                "freshness": score.freshness_score,
                "latency": score.latency_score,
            })

        rankings.sort(key=lambda x: x["reliability_score"], reverse=True)
        return rankings

    def _get_or_create_metrics(self, source_id: str) -> SourceMetrics:
        """Get or create metrics for current period."""
        metrics_list = self._metrics.setdefault(source_id, [])

        # Get current period (last 24h)
        now = datetime.utcnow()
        if metrics_list:
            current = metrics_list[-1]
            if (now - current.period_start).total_seconds() < 86400:
                return current

        # Create new period
        new_metrics = SourceMetrics(source_id=source_id, period_start=now)
        metrics_list.append(new_metrics)

        # Keep only last 30 periods
        if len(metrics_list) > 30:
            self._metrics[source_id] = metrics_list[-30:]

        return new_metrics

    def _calculate_accuracy(self, metrics: SourceMetrics) -> float:
        """Calculate accuracy score from metrics."""
        if metrics.total_extracted == 0:
            return 50.0  # Default

        verified_rate = metrics.verified_extracted / metrics.total_extracted
        conflict_rate = metrics.conflicted_extracted / metrics.total_extracted
        fabrication_rate = metrics.fabricated_detected / metrics.total_extracted

        # Score: high verified = good, high conflict/fabrication = bad
        score = 50.0
        score += verified_rate * 40  # Up to +40
        score -= conflict_rate * 30  # Up to -30
        score -= fabrication_rate * 50  # Up to -50

        return max(0, min(100, score))

    def _calculate_coverage(self, metrics: SourceMetrics) -> float:
        """Calculate coverage score from metrics."""
        if metrics.total_requests == 0:
            return 50.0

        # More requests with results = better coverage
        success_rate = metrics.successful_requests / metrics.total_requests
        extraction_rate = metrics.total_extracted / max(1, metrics.successful_requests)

        score = 50.0
        score += success_rate * 25
        score += min(25, extraction_rate * 5)  # Cap at 25

        return max(0, min(100, score))

    def _calculate_freshness(self, source_id: str) -> float:
        """Calculate freshness score based on last successful request."""
        metrics_list = self._metrics.get(source_id, [])
        if not metrics_list:
            return 50.0

        # Find last successful request
        for metrics in reversed(metrics_list):
            if metrics.successful_requests > 0:
                hours_since = (datetime.utcnow() - metrics.period_start).total_seconds() / 3600
                if hours_since < 24:
                    return 90.0
                elif hours_since < 72:
                    return 70.0
                elif hours_since < 168:
                    return 50.0
                else:
                    return 30.0

        return 20.0

    def _calculate_latency(self, metrics: SourceMetrics) -> float:
        """Calculate latency score (lower is better)."""
        if metrics.avg_latency_ms == 0:
            return 50.0

        if metrics.avg_latency_ms < 1000:
            return 90.0
        elif metrics.avg_latency_ms < 3000:
            return 70.0
        elif metrics.avg_latency_ms < 5000:
            return 50.0
        elif metrics.avg_latency_ms < 10000:
            return 30.0
        else:
            return 10.0
