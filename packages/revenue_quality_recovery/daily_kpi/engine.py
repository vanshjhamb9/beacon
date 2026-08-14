from __future__ import annotations

from typing import Any

from revenue_quality_recovery.models.types import DailyKpiReport, RevenueVerdict, RqpSnapshot, SurfaceStatus


class DailyKpiEngine:
    """Rule 10 — daily revenue-quality KPIs."""

    def compute(
        self,
        snapshots: list[RqpSnapshot] | list[dict[str, Any]],
        *,
        collected_today: int | None = None,
        duplicates: int = 0,
        fake_companies: int = 0,
    ) -> DailyKpiReport:
        rows = [self._as_dict(s) for s in snapshots]
        n = len(rows)
        if n == 0:
            return DailyKpiReport(
                collected_today=collected_today or 0,
                duplicates=duplicates,
                fake_companies=fake_companies,
            )

        rejected = sum(1 for r in rows if r.get("verdict") == RevenueVerdict.REJECTED.value)
        sales_ready = sum(1 for r in rows if r.get("verdict") == RevenueVerdict.SALES_READY.value)
        recovered = sum(
            1
            for r in rows
            if self._nested(r, "identity", "accepted") or self._nested(r, "sales_ready_gate", "complete")
        )
        identity = sum(1 for r in rows if self._nested(r, "identity", "accepted"))
        website = sum(
            1
            for r in rows
            if self._nested(r, "identity", "checks", "website_alive")
            or (isinstance(self._nested(r, "profile", "website"), str) and self._nested(r, "profile", "website") not in (None, "UNKNOWN"))
        )
        # Fix website check - use simpler approach
        website = sum(1 for r in rows if self._has_website(r))
        contacts = sum(
            1
            for r in rows
            if int(self._nested(r, "contacts", "verified_email_count") or 0) > 0
            or int(self._nested(r, "contacts", "verified_phone_count") or 0) > 0
        )
        dms = sum(1 for r in rows if len(self._nested(r, "contacts", "contacts") or []) > 0)
        enterprise = sum(
            1
            for r in rows
            if self._nested(r, "surface", "status") == SurfaceStatus.ENTERPRISE_READY.value
        )
        confs = [float(r.get("confidence") or 0) for r in rows]
        avg_conf = round(sum(confs) / len(confs), 2) if confs else 0.0

        def pct(c: int) -> float:
            return round(100.0 * c / n, 2)

        return DailyKpiReport(
            collected_today=collected_today if collected_today is not None else n,
            rejected_today=rejected,
            recovered_today=recovered,
            identity_percent=pct(identity),
            website_percent=pct(website),
            contacts_percent=pct(contacts),
            decision_makers_percent=pct(dms),
            sales_ready_percent=pct(sales_ready),
            enterprise_percent=pct(enterprise),
            average_confidence=avg_conf,
            duplicates=duplicates,
            fake_companies=fake_companies,
            scoring_version="rqp-v1",
        )

    def _as_dict(self, snap: RqpSnapshot | dict[str, Any]) -> dict[str, Any]:
        if isinstance(snap, RqpSnapshot):
            return snap.model_dump(mode="json")
        return dict(snap)

    def _nested(self, row: dict[str, Any], *keys: str) -> Any:
        cur: Any = row
        for k in keys:
            if not isinstance(cur, dict):
                return None
            cur = cur.get(k)
        return cur

    def _has_website(self, row: dict[str, Any]) -> bool:
        profile = row.get("profile") or {}
        if isinstance(profile, dict):
            site = profile.get("website")
            if site and site != "UNKNOWN":
                return True
        checks = self._nested(row, "identity", "checks") or {}
        if isinstance(checks, dict) and checks.get("website_alive"):
            return True
        return False
