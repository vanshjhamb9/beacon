"""Overall pipeline / connector / worker health summary."""

from __future__ import annotations

from operations_center.models import (
    ConnectorHealthView,
    ConversionStep,
    HealthSummary,
    WorkerHealthView,
)
from operations_center.pipeline_monitor import biggest_bottleneck


def evaluate_health(
    *,
    signals_today: int,
    connectors: list[ConnectorHealthView],
    workers: list[WorkerHealthView],
    conversions: list[ConversionStep],
) -> HealthSummary:
    enabled = [c for c in connectors if c.enabled]
    healthy_connectors = [c for c in enabled if c.healthy]
    running_workers = [w for w in workers if w.running]
    collecting = signals_today > 0 or any(c.records_today > 0 for c in enabled)

    bottleneck = biggest_bottleneck(conversions)
    failing_connectors = [c for c in enabled if not c.healthy]
    offline_workers = [w for w in workers if not w.running]

    if collecting and not failing_connectors and not offline_workers:
        tone = "GREEN"
        summary = "Beacon is collecting and the pipeline is healthy."
        pipeline_healthy = True
    elif collecting and (failing_connectors or offline_workers):
        tone = "YELLOW"
        bits = []
        if failing_connectors:
            bits.append(f"{len(failing_connectors)} connector(s) unhealthy")
        if offline_workers:
            bits.append(f"{len(offline_workers)} worker(s) offline")
        summary = "Beacon is collecting with issues: " + "; ".join(bits) + "."
        pipeline_healthy = False
    elif running_workers and not collecting:
        # Quiet day ≠ outage when workers are online.
        tone = "YELLOW"
        summary = (
            "Workers are online but no new signals today — pipeline is idle, not down."
        )
        pipeline_healthy = True
    else:
        tone = "RED"
        summary = "Beacon is not collecting data right now."
        pipeline_healthy = False

    if bottleneck:
        summary = f"{summary} Biggest bottleneck: {bottleneck}."

    return HealthSummary(
        collecting=collecting,
        pipeline_healthy=pipeline_healthy,
        connectors_healthy=len(healthy_connectors),
        connectors_total=len(enabled) or len(connectors),
        workers_running=len(running_workers),
        workers_total=len(workers),
        biggest_bottleneck=bottleneck,
        tone=tone,
        summary=summary,
    )
