from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from runtime_ops.models.types import RuntimeOpsSnapshot


class RuntimeOpsReportBuilder:
    """Deterministic markdown reports from a RuntimeOpsSnapshot."""

    def build_all(self, snapshot: RuntimeOpsSnapshot) -> dict[str, str]:
        return {
            "platform_health": self.platform_health(snapshot),
            "infrastructure": self.infrastructure(snapshot),
            "collectors": self.collectors(snapshot),
            "pipeline": self.pipeline(snapshot),
            "migrations": self.migrations(snapshot),
            "coverage": self.coverage(snapshot),
            "freshness": self.freshness(snapshot),
            "performance": self.performance(snapshot),
            "production_readiness": self.production_readiness(snapshot),
        }

    def platform_health(self, s: RuntimeOpsSnapshot) -> str:
        return self._section(
            "Platform Health Report",
            status="PASS" if s.readiness_score >= 95 and s.production_gate.allow_production else "FAIL",
            evidence=s.production_gate.evidence,
            metrics={"readiness_score": s.readiness_score, "alerts": len(s.alerts)},
            recommendations=[a.recommended_fix for a in s.alerts[:8]],
        )

    def infrastructure(self, s: RuntimeOpsSnapshot) -> str:
        return self._section(
            "Infrastructure Report",
            status="PASS" if s.redis.ok and s.celery.broker_ok else "FAIL",
            evidence=s.redis.evidence + s.celery.evidence,
            metrics={
                "redis_version": s.redis.version,
                "redis_ok": s.redis.ok,
                "worker_online": s.celery.worker_online,
                "beat_online": s.celery.beat_online,
                "queue_depth": s.celery.queue_depth,
            },
            recommendations=[
                a.recommended_fix
                for a in s.alerts
                if a.code in {"worker_offline", "beat_offline", "redis_streams_unsupported", "queue_stalled"}
            ],
        )

    def collectors(self, s: RuntimeOpsSnapshot) -> str:
        failing = [c.get("source") for c in s.collectors if c.get("health_status") in {"DOWN", "down", "DEGRADED", "degraded"}]
        return self._section(
            "Collector Health Report",
            status="PASS" if not failing else "WARNING",
            evidence=[f"collectors:{len(s.collectors)}", f"failing:{failing}"],
            metrics={"collector_count": len(s.collectors), "failing": len(failing)},
            recommendations=["Re-enable Beat/Worker and re-run failing connectors"],
        )

    def pipeline(self, s: RuntimeOpsSnapshot) -> str:
        fail = [p.stage for p in s.pipeline if p.status.value == "fail"]
        return self._section(
            "Pipeline Validation Report",
            status="PASS" if not fail else "FAIL",
            evidence=[f"{p.stage}:{p.success_percent}%" for p in s.pipeline],
            metrics={"stages": len(s.pipeline), "failing_stages": len(fail)},
            recommendations=["Investigate failing stage worker tasks and input coverage"],
        )

    def migrations(self, s: RuntimeOpsSnapshot) -> str:
        return self._section(
            "Migration Validation Report",
            status="PASS" if s.migrations.ok else "FAIL",
            evidence=s.migrations.evidence,
            metrics={
                "current": s.migrations.current_revision,
                "head": s.migrations.head_revision,
                "pending": len(s.migrations.pending_revisions),
                "missing_tables": len(s.migrations.missing_tables),
            },
            recommendations=["alembic upgrade head"] if not s.migrations.ok else ["None"],
        )

    def coverage(self, s: RuntimeOpsSnapshot) -> str:
        return self._section(
            "Coverage Report",
            status="PASS" if float(s.enrichment.get("coverage_pct", 0)) >= 50 else "WARNING",
            evidence=[f"{k}:{v}" for k, v in list(s.enrichment.items())[:12]],
            metrics=dict(s.enrichment),
            recommendations=["Raise enrichment throughput for qualified opportunities"],
        )

    def freshness(self, s: RuntimeOpsSnapshot) -> str:
        return self._section(
            "Freshness Report",
            status="PASS",
            evidence=[f"{k}:{v}" for k, v in list(s.freshness.items())[:12]],
            metrics=dict(s.freshness),
            recommendations=["Keep Beat online to maintain freshness SLAs"],
        )

    def performance(self, s: RuntimeOpsSnapshot) -> str:
        return self._section(
            "Performance Benchmark Report",
            status="PASS" if (s.redis.latency_ms or 999) < 300 else "WARNING",
            evidence=[f"redis_latency_ms:{s.redis.latency_ms}"],
            metrics={"redis_latency_ms": s.redis.latency_ms, "queue_depth": s.celery.queue_depth},
            recommendations=["Health API target <300ms; collector cycle <5m"],
        )

    def production_readiness(self, s: RuntimeOpsSnapshot) -> str:
        return self._section(
            "Production Readiness Report",
            status="PASS" if s.production_gate.allow_production and s.production_gate.score >= 95 else "FAIL",
            evidence=s.production_gate.evidence + s.production_gate.blockers,
            metrics={"score": s.production_gate.score, "allow": s.production_gate.allow_production},
            recommendations=s.production_gate.blockers or ["Ready for production mode"],
        )

    def _section(
        self,
        title: str,
        *,
        status: str,
        evidence: list[Any],
        metrics: dict[str, Any],
        recommendations: list[str],
    ) -> str:
        lines = [
            f"# {title}",
            "",
            f"**Generated:** {datetime.now(UTC).isoformat()}",
            f"**Status:** {status}",
            "",
            "## Metrics",
        ]
        for k, v in metrics.items():
            lines.append(f"- {k}: {v}")
        lines.extend(["", "## Evidence"])
        for item in evidence:
            lines.append(f"- {item}")
        lines.extend(["", "## Recommendations"])
        for item in recommendations:
            lines.append(f"- {item}")
        lines.append("")
        return "\n".join(lines)
