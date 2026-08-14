"""Metrics helpers — deltas, trends, revenue projections."""

from __future__ import annotations

from operations_center.models import RevenueEngineView, StageMetric, TodayProgress


def today_progress(*, started: int, current: int) -> TodayProgress:
    return TodayProgress(
        started_revenue_ready=max(started, 0),
        current_revenue_ready=max(current, 0),
        difference=current - started,
    )


def revenue_engine(
    *,
    pipeline_value: float,
    meetings: int,
    won: int,
    projected_multiplier: float = 1.4,
) -> RevenueEngineView:
    pipeline = max(float(pipeline_value or 0.0), 0.0)
    return RevenueEngineView(
        pipeline=round(pipeline, 2),
        projected=round(pipeline * projected_multiplier, 2),
        meetings=max(int(meetings or 0), 0),
        won=max(int(won or 0), 0),
    )


def top_row_cards(
    stages: list[StageMetric],
    *,
    pipeline_value: float,
    meetings: int,
) -> dict[str, object]:
    by_stage = {s.stage: s for s in stages}

    def _card(stage: str) -> dict[str, object]:
        s = by_stage.get(stage)
        if not s:
            return {"current": 0, "today": 0, "delta_pct": None}
        return {
            "current": s.current,
            "today": s.today,
            "yesterday": s.yesterday,
            "delta_pct": s.delta_pct,
            "trend_7d": s.trend_7d,
        }

    return {
        "signals": _card("signals"),
        "verified": _card("verified_websites"),
        "emails": _card("emails"),
        "decision_makers": _card("decision_makers"),
        "sales_ready": _card("sales_ready"),
        "revenue_ready": _card("revenue_ready"),
        "meetings": {
            "current": meetings,
            "today": by_stage.get("meetings").today if by_stage.get("meetings") else 0,
            "delta_pct": by_stage.get("meetings").delta_pct if by_stage.get("meetings") else None,
        },
        "pipeline": {"value": round(pipeline_value, 2)},
    }


def pct_change(current: int, previous: int) -> float | None:
    if previous <= 0:
        return 100.0 if current > 0 else None
    return round(((current - previous) / previous) * 100.0, 1)
