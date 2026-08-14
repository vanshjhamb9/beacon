from __future__ import annotations

from time import perf_counter
from typing import Any, Callable

from revenue_data_recovery.models.types import DailyRecoveryReport, RecoveryStage, RdiSnapshot
from revenue_data_recovery.pipelines.engine import RevenueDataRecoveryPipeline


class DailyRecoveryWorker:
    """Recover old companies every day — never stop improving coverage."""

    def __init__(self, pipeline: RevenueDataRecoveryPipeline | None = None) -> None:
        self.pipeline = pipeline or RevenueDataRecoveryPipeline()

    def run(
        self,
        payloads: list[dict[str, Any]],
        *,
        on_result: Callable[[RdiSnapshot], None] | None = None,
    ) -> DailyRecoveryReport:
        started = perf_counter()
        recovered = 0
        failed = 0
        fake_eliminated = 0
        sales_ready = 0
        stages: dict[str, int] = {}

        for payload in payloads:
            try:
                snap = self.pipeline.evaluate(payload)
            except Exception:  # noqa: BLE001 — isolate bad rows; keep batch moving
                failed += 1
                continue
            if on_result:
                on_result(snap)
            stage = snap.recovery_stage.value
            stages[stage] = stages.get(stage, 0) + 1
            if snap.fake.is_fake:
                fake_eliminated += 1
            if snap.identity.identity_complete or snap.website.website_verified or snap.contacts.contacts:
                recovered += 1
            if snap.eligible_for_revenue_hunter or snap.status.value == "SALES_READY":
                sales_ready += 1
            if snap.recovery_stage == RecoveryStage.REJECTED:
                failed += 1

        duration_ms = (perf_counter() - started) * 1000.0
        return DailyRecoveryReport(
            processed=len(payloads),
            recovered=recovered,
            failed=failed,
            fake_eliminated=fake_eliminated,
            sales_ready=sales_ready,
            stages=stages,
            duration_ms=round(duration_ms, 2),
            scoring_version="rdi-v1",
        )
