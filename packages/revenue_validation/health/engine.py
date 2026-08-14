"""Production readiness health — GREEN / YELLOW / RED."""

from __future__ import annotations

from typing import Any

from revenue_validation.models.types import HealthTone, ProductionHealth


class ProductionHealthEngine:
    def evaluate(self, metrics: dict[str, Any]) -> list[dict[str, Any]]:
        rr = int(metrics.get("revenue_ready") or 0)
        contacted = int(metrics.get("contacted") or 0)
        replies = int(metrics.get("replies") or 0)
        meetings = int(metrics.get("meetings") or 0)
        won = int(metrics.get("won") or 0)
        revenue = float(metrics.get("revenue") or 0)
        dup = float(metrics.get("duplicate_pct") or 0)
        fabricated = int(metrics.get("fabricated_data") or 0)
        pred = float(metrics.get("prediction_accuracy") or 0)
        dm_acc = float(metrics.get("decision_maker_accuracy") or 0)
        attr_cov = float(metrics.get("revenue_attribution_coverage") or 0)

        items = [
            self._kpi("Revenue Ready", rr, green=10, yellow=5),
            self._kpi("Contacted", contacted, green=10, yellow=3),
            self._kpi("Replies", replies, green=3, yellow=1),
            self._kpi("Meetings", meetings, green=2, yellow=1),
            self._kpi("Won", won, green=1, yellow=0),
            ProductionHealth(
                metric="Revenue",
                value=revenue,
                tone=HealthTone.GREEN if revenue > 0 else HealthTone.YELLOW if contacted >= 10 else HealthTone.RED,
                detail="Actual closed revenue only",
            ),
            ProductionHealth(
                metric="Duplicate %",
                value=dup,
                tone=HealthTone.GREEN if dup <= 5 else HealthTone.YELLOW if dup <= 15 else HealthTone.RED,
            ),
            ProductionHealth(
                metric="Fabricated Data",
                value=fabricated,
                tone=HealthTone.GREEN if fabricated == 0 else HealthTone.RED,
                detail="Must remain 0",
            ),
            ProductionHealth(
                metric="Prediction Accuracy",
                value=pred,
                tone=HealthTone.GREEN if pred >= 70 else HealthTone.YELLOW if pred >= 40 or pred == 0 else HealthTone.RED,
                detail="0 until founder validates predictions",
            ),
            ProductionHealth(
                metric="Decision Maker Accuracy",
                value=dm_acc,
                tone=HealthTone.GREEN if dm_acc >= 70 else HealthTone.YELLOW if dm_acc >= 40 or dm_acc == 0 else HealthTone.RED,
            ),
            ProductionHealth(
                metric="Revenue Attribution Coverage",
                value=attr_cov,
                tone=HealthTone.GREEN if attr_cov >= 100 else HealthTone.YELLOW if attr_cov >= 80 else HealthTone.RED,
            ),
        ]
        return [i.model_dump(mode="json") for i in items]

    def _kpi(self, name: str, value: int, *, green: int, yellow: int) -> ProductionHealth:
        if value >= green:
            tone = HealthTone.GREEN
        elif value >= yellow:
            tone = HealthTone.YELLOW
        else:
            tone = HealthTone.RED
        return ProductionHealth(metric=name, value=value, tone=tone)
