from __future__ import annotations

from typing import Any

from revenue_data_recovery.models.types import RecoveryMetrics, RdiSnapshot, RecoveryStage


class RecoveryMetricsEngine:
    """Internal QA metrics for RDI — engineering only."""

    def aggregate(
        self,
        snapshots: list[RdiSnapshot] | list[dict[str, Any]],
        *,
        recovery_time_ms: float = 0.0,
        duplicate_percent: float = 0.0,
    ) -> RecoveryMetrics:
        rows = [self._as_dict(s) for s in snapshots]
        n = len(rows)
        if n == 0:
            return RecoveryMetrics(duplicate_percent=duplicate_percent, recovery_time_ms=recovery_time_ms)

        identity_complete = sum(1 for r in rows if self._nested(r, "identity", "identity_complete"))
        website_verified = sum(1 for r in rows if self._nested(r, "website", "website_verified"))
        intent_ok = sum(1 for r in rows if float(self._nested(r, "intent", "score") or 0) >= 25)
        contacts_ok = sum(
            1
            for r in rows
            if int(self._nested(r, "contacts", "verified_email_count") or 0) > 0
            or int(self._nested(r, "contacts", "verified_decision_maker_count") or 0) > 0
            or int(self._nested(r, "contacts", "verified_phone_count") or 0) > 0
        )
        sales_ready = sum(1 for r in rows if r.get("status") == "SALES_READY" or r.get("eligible_for_revenue_hunter"))
        fake = sum(1 for r in rows if self._nested(r, "fake", "is_fake"))
        founder = sum(1 for r in rows if r.get("visible_in_founder_queue"))
        failures = sum(1 for r in rows if r.get("recovery_stage") == RecoveryStage.REJECTED.value or self._nested(r, "fake", "is_fake"))
        success = sum(
            1
            for r in rows
            if self._nested(r, "identity", "identity_complete") and self._nested(r, "website", "website_verified")
        )
        unknown_fields = 0
        for r in rows:
            missing = self._nested(r, "identity", "missing_fields") or []
            if isinstance(missing, list):
                unknown_fields += len(missing)

        def pct(count: int) -> float:
            return round(100.0 * count / n, 2)

        recovery_percent = pct(success)

        return RecoveryMetrics(
            companies=n,
            identity_complete=identity_complete,
            identity_percent=pct(identity_complete),
            website_verified=website_verified,
            website_percent=pct(website_verified),
            intent_above_threshold=intent_ok,
            intent_percent=pct(intent_ok),
            contacts_with_path=contacts_ok,
            contacts_percent=pct(contacts_ok),
            sales_ready=sales_ready,
            sales_ready_percent=pct(sales_ready),
            recovery_percent=recovery_percent,
            recovery_failures=failures,
            unknown_fields=unknown_fields,
            fake_companies=fake,
            duplicate_percent=round(duplicate_percent, 2),
            recovery_time_ms=round(recovery_time_ms, 2),
            recovery_success=success,
            founder_queue=founder,
            scoring_version="rdi-v1",
        )

    def _as_dict(self, snap: RdiSnapshot | dict[str, Any]) -> dict[str, Any]:
        if isinstance(snap, RdiSnapshot):
            return snap.model_dump(mode="json")
        return dict(snap)

    def _nested(self, row: dict[str, Any], a: str, b: str) -> Any:
        block = row.get(a)
        if isinstance(block, dict):
            return block.get(b)
        return None
