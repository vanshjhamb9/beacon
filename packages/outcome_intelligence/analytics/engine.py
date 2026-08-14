from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from statistics import mean
from typing import Any

from outcome_intelligence.metrics.lifecycle import outcome_score, stage_order
from outcome_intelligence.models.types import (
    DimensionRevenue,
    FunnelStageMetric,
    OutcomeLifecycle,
    RateMetrics,
    RevenueMetrics,
)


class OutcomeAnalyticsEngine:
    def funnel(self, stages: list[str]) -> list[FunnelStageMetric]:
        counts: dict[str, int] = defaultdict(int)
        for stage in stages:
            counts[stage] += 1
        metrics: list[FunnelStageMetric] = []
        previous = 0
        for index, stage in enumerate(stage_order()):
            count = counts.get(stage.value, 0)
            conversion = 100.0 if index == 0 or previous <= 0 else round((count / previous) * 100.0, 4)
            # cumulative-style: count opportunities that reached at least this stage
            reached = sum(
                counts.get(item.value, 0)
                for item in stage_order()
                if self._rank(item) >= self._rank(stage) and item not in {OutcomeLifecycle.LOST, OutcomeLifecycle.ARCHIVED}
            )
            if stage in {OutcomeLifecycle.LOST, OutcomeLifecycle.ARCHIVED, OutcomeLifecycle.WON}:
                reached = count
            metrics.append(
                FunnelStageMetric(
                    stage=stage.value,
                    count=reached if stage not in {OutcomeLifecycle.LOST, OutcomeLifecycle.ARCHIVED} else count,
                    conversion_from_previous=conversion if index > 0 else 100.0,
                )
            )
            previous = max(reached, 1)
        return metrics

    def rates(self, records: list[dict[str, Any]]) -> RateMetrics:
        total = max(len(records), 1)
        contacted = sum(1 for row in records if self._reached(row, OutcomeLifecycle.CONTACTED))
        replied = sum(1 for row in records if self._reached(row, OutcomeLifecycle.REPLIED))
        meetings = sum(1 for row in records if self._reached(row, OutcomeLifecycle.MEETING_SCHEDULED))
        proposals = sum(1 for row in records if self._reached(row, OutcomeLifecycle.PROPOSAL_SENT))
        won = sum(1 for row in records if row.get("lifecycle_stage") == OutcomeLifecycle.WON.value)
        lost = sum(1 for row in records if row.get("lifecycle_stage") == OutcomeLifecycle.LOST.value)
        denom_contact = max(contacted, 1)
        return RateMetrics(
            meeting_rate=round(meetings / denom_contact * 100.0, 4),
            reply_rate=round(replied / denom_contact * 100.0, 4),
            proposal_rate=round(proposals / denom_contact * 100.0, 4),
            close_rate=round(won / max(contacted, 1) * 100.0, 4),
            contacted_count=contacted,
            replied_count=replied,
            meeting_count=meetings,
            proposal_count=proposals,
            won_count=won,
            lost_count=lost,
            total_opportunities=len(records),
        )

    def revenue(self, records: list[dict[str, Any]]) -> RevenueMetrics:
        won_rows = [row for row in records if row.get("lifecycle_stage") == OutcomeLifecycle.WON.value]
        revenues = [float(row.get("revenue") or row.get("deal_value") or 0.0) for row in won_rows]
        cycles: list[float] = []
        for row in won_rows:
            created = row.get("created_at")
            closed = row.get("close_date") or row.get("updated_at")
            if isinstance(created, datetime) and isinstance(closed, datetime):
                cycles.append(max((closed - created).total_seconds() / 86400.0, 0.0))
        open_pipeline = sum(
            float(row.get("proposal_value") or row.get("revenue") or 0.0)
            for row in records
            if row.get("lifecycle_stage")
            in {
                OutcomeLifecycle.PROPOSAL_SENT.value,
                OutcomeLifecycle.NEGOTIATION.value,
                OutcomeLifecycle.QUALIFIED.value,
            }
        )
        return RevenueMetrics(
            total_revenue=round(sum(revenues), 4),
            average_deal_size=round(mean(revenues), 4) if revenues else 0.0,
            average_sales_cycle_days=round(mean(cycles), 4) if cycles else 0.0,
            open_pipeline_value=round(open_pipeline, 4),
            won_deals=len(won_rows),
        )

    def revenue_by_dimension(self, records: list[dict[str, Any]], dimension: str) -> list[DimensionRevenue]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in records:
            key = str(row.get(dimension) or "unknown")
            grouped[key].append(row)
        result: list[DimensionRevenue] = []
        for key, rows in grouped.items():
            won = [row for row in rows if row.get("lifecycle_stage") == OutcomeLifecycle.WON.value]
            revenue = sum(float(row.get("revenue") or row.get("deal_value") or 0.0) for row in won)
            result.append(
                DimensionRevenue(
                    dimension=dimension,
                    key=key,
                    revenue=round(revenue, 4),
                    deals=len(won),
                    average_deal_size=round(revenue / len(won), 4) if won else 0.0,
                    win_rate=round(len(won) / max(len(rows), 1) * 100.0, 4),
                )
            )
        return sorted(result, key=lambda item: item.revenue, reverse=True)

    def _reached(self, row: dict[str, Any], stage: OutcomeLifecycle) -> bool:
        current = str(row.get("lifecycle_stage") or OutcomeLifecycle.NEW.value)
        if current in {OutcomeLifecycle.LOST.value, OutcomeLifecycle.ARCHIVED.value}:
            # Still count historical progress flags when present.
            flags = {
                OutcomeLifecycle.CONTACTED: row.get("contacted_at") is not None,
                OutcomeLifecycle.REPLIED: row.get("replied_at") is not None,
                OutcomeLifecycle.MEETING_SCHEDULED: row.get("meeting_at") is not None,
                OutcomeLifecycle.PROPOSAL_SENT: row.get("proposal_at") is not None,
            }
            return bool(flags.get(stage, False)) or self._rank_str(current) >= self._rank(stage)
        return self._rank_str(current) >= self._rank(stage)

    def _rank(self, stage: OutcomeLifecycle) -> int:
        try:
            return stage_order().index(stage)
        except ValueError:
            return 0

    def _rank_str(self, stage: str) -> int:
        try:
            return self._rank(OutcomeLifecycle(stage))
        except ValueError:
            return int(outcome_score(stage) // 10)
