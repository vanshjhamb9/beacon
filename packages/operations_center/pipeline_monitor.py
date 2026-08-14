"""Pipeline stage counters and conversion math."""

from __future__ import annotations

from operations_center.models import (
    PIPELINE_STAGES,
    ConversionStep,
    StageMetric,
)


def build_stage_metrics(
    *,
    current: dict[str, int],
    today: dict[str, int],
    yesterday: dict[str, int],
    hour: dict[str, int],
    trends: dict[str, list[int]] | None = None,
) -> list[StageMetric]:
    trends = trends or {}
    out: list[StageMetric] = []
    for stage in PIPELINE_STAGES:
        today_n = int(today.get(stage, 0) or 0)
        yday_n = int(yesterday.get(stage, 0) or 0)
        delta = None
        if yday_n > 0:
            delta = round(((today_n - yday_n) / yday_n) * 100.0, 1)
        elif today_n > 0:
            delta = 100.0
        out.append(
            StageMetric(
                stage=stage,
                current=int(current.get(stage, 0) or 0),
                today=today_n,
                yesterday=yday_n,
                hour=int(hour.get(stage, 0) or 0),
                trend_7d=list(trends.get(stage, [])),
                delta_pct=delta,
            )
        )
    return out


def conversion_chain(stages: list[StageMetric]) -> list[ConversionStep]:
    """Compute stage→stage conversion and drop percentages.

    Honest rules:
    - from=0, to=0 → idle (0/0)
    - from=0, to>0 → downstream-only / bypass (not a 100% drop)
    - to > from → expansion capped at 100% conversion, 0% drop
    - otherwise standard conversion/drop
    """
    steps: list[ConversionStep] = []
    for i in range(len(stages) - 1):
        upstream = stages[i]
        downstream = stages[i + 1]
        from_count = max(upstream.current, 0)
        to_count = max(downstream.current, 0)
        if from_count <= 0 and to_count <= 0:
            conversion = 0.0
            drop = 0.0
        elif from_count <= 0 and to_count > 0:
            # Downstream populated without this upstream — not a pipeline drop.
            conversion = 100.0
            drop = 0.0
        elif to_count >= from_count:
            conversion = 100.0
            drop = 0.0
        else:
            conversion = round((to_count / from_count) * 100.0, 1)
            drop = round(((from_count - to_count) / from_count) * 100.0, 1)
        steps.append(
            ConversionStep(
                from_stage=upstream.stage,
                to_stage=downstream.stage,
                from_count=from_count,
                to_count=to_count,
                conversion_pct=conversion,
                drop_pct=drop,
            )
        )
    return steps


def biggest_bottleneck(steps: list[ConversionStep]) -> str | None:
    if not steps:
        return None
    # Ignore idle and bypass steps (no real upstream volume).
    candidates = [s for s in steps if s.from_count >= 5 and s.drop_pct > 0]
    if not candidates:
        return None
    worst = max(candidates, key=lambda s: s.drop_pct)
    return f"{worst.from_stage} -> {worst.to_stage} ({worst.drop_pct}% drop)"
