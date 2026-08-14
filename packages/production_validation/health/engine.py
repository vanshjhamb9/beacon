from __future__ import annotations

from production_validation.models.types import ComponentHealth, EngineHealthReport, HealthStatus, ProductionValidationInput


class HealthEngine:
    """Compose component health from operational signals (no new collectors)."""

    DEFAULT_COMPONENTS = (
        "api",
        "workers",
        "collectors",
        "campaigns",
        "email",
        "whatsapp",
        "oauth",
        "queues",
        "database",
        "redis",
        "celery",
        "pipeline",
    )

    def evaluate(self, item: ProductionValidationInput) -> EngineHealthReport:
        components: list[ComponentHealth] = []
        for name in self.DEFAULT_COMPONENTS:
            signal = dict(item.component_signals.get(name) or {})
            if name == "oauth":
                signal.setdefault("success_rate", 100.0 if item.oauth_ok else 0.0)
                signal.setdefault("failure_rate", 0.0 if item.oauth_ok else 100.0)
            if name == "workers" or name == "celery":
                signal.setdefault("success_rate", 100.0 if item.workers_online else 0.0)
            if name == "queues":
                signal.setdefault("queue_depth", item.queue_depth)
                signal.setdefault("failure_rate", 40.0 if item.queue_depth > 500 else 0.0)
            if name == "email":
                signal.setdefault("failure_rate", min(100.0, item.bounce_rate * 100))
                signal.setdefault("success_rate", max(0.0, 100.0 - item.bounce_rate * 100))
            components.append(self._component(name, signal))

        score = sum(self._status_score(c.status) for c in components) / max(len(components), 1)
        overall = (
            HealthStatus.PASS
            if score >= 85
            else HealthStatus.WARNING
            if score >= 60
            else HealthStatus.FAIL
        )
        return EngineHealthReport(
            components=components,
            overall_status=overall,
            overall_score=round(score, 4),
            evidence=[f"components:{len(components)}", f"overall:{overall.value}"],
        )

    def _component(self, name: str, signal: dict) -> ComponentHealth:
        success = float(signal.get("success_rate", 95.0))
        failure = float(signal.get("failure_rate", max(0.0, 100.0 - success)))
        latency = float(signal.get("latency_ms", 120.0))
        queue_depth = int(signal.get("queue_depth", 0))
        status = HealthStatus.PASS
        recommendation = None
        if failure >= 25 or success < 70 or latency > 2000 or queue_depth > 1000:
            status = HealthStatus.FAIL
            recommendation = f"Investigate {name} failures and clear backlog."
        elif failure >= 10 or success < 85 or latency > 800 or queue_depth > 200:
            status = HealthStatus.WARNING
            recommendation = f"Monitor {name}; consider scaling or retries."
        return ComponentHealth(
            name=name,
            status=status,
            latency_ms=latency,
            throughput=float(signal.get("throughput", 0.0)),
            failure_rate=round(failure, 4),
            success_rate=round(success, 4),
            retry_count=int(signal.get("retry_count", 0)),
            queue_depth=queue_depth,
            accuracy=float(signal["accuracy"]) if signal.get("accuracy") is not None else None,
            evidence=[f"{k}:{v}" for k, v in list(signal.items())[:8]],
            recommendation=recommendation,
        )

    def _status_score(self, status: HealthStatus) -> float:
        return {HealthStatus.PASS: 100.0, HealthStatus.WARNING: 70.0, HealthStatus.FAIL: 30.0}.get(status, 50.0)
