from __future__ import annotations

from typing import Any

from testing_platform.models.types import ComponentHealth, SystemHealthReport


class SystemHealthBuilder:
    def build(self, probes: dict[str, dict[str, Any]], *, mode: str = "sandbox") -> SystemHealthReport:
        components: list[ComponentHealth] = []
        for name, probe in probes.items():
            status = str(probe.get("status") or "unknown")
            score = float(probe.get("score") if probe.get("score") is not None else (100.0 if status == "ok" else 40.0))
            components.append(
                ComponentHealth(
                    name=name,
                    status=status,
                    score=score,
                    latency_ms=probe.get("latency_ms"),
                    details={k: v for k, v in probe.items() if k not in {"status", "score", "latency_ms"}},
                )
            )
        overall = round(sum(item.score for item in components) / max(1, len(components)), 2)
        status = "ok" if overall >= 80 else "degraded" if overall >= 50 else "critical"
        recommendations: list[str] = []
        if mode != "sandbox":
            recommendations.append("Production send enabled — verify OAuth tokens and quotas.")
        for item in components:
            if item.status != "ok":
                recommendations.append(f"Investigate {item.name}: status={item.status}")
        return SystemHealthReport(
            overall_score=overall,
            status=status,
            components=components,
            mode=mode,
            recommendations=recommendations,
        )
