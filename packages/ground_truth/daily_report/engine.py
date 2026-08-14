from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from ground_truth.models.types import DailyImprovementReport, GtSnapshot, GtVerdict, QualityFunnel, UNKNOWN


class DailyImprovementReportEngine:
    """Rule 10 — midnight morning report."""

    def build(
        self,
        snapshots: list[GtSnapshot] | list[dict[str, Any]],
        *,
        funnel: QualityFunnel | None = None,
        duplicates_merged: int = 0,
        date: str | None = None,
    ) -> DailyImprovementReport:
        rows = [s.model_dump(mode="json") if isinstance(s, GtSnapshot) else dict(s) for s in snapshots]
        n = len(rows)
        rejected = sum(1 for r in rows if r.get("verdict") == GtVerdict.REJECTED.value)
        sales = sum(1 for r in rows if r.get("verdict") == GtVerdict.SALES_READY.value)
        enterprise = sum(1 for r in rows if r.get("verdict") == GtVerdict.ENTERPRISE_READY.value)
        passed = sales + enterprise

        emails = 0
        phones = 0
        for r in rows:
            contacts = r.get("contacts") or {}
            emails += len(contacts.get("emails") or [])
            phones += len(contacts.get("phones") or [])

        fake = funnel.fake if funnel else sum(
            1 for r in rows if "Fake" in str(((r.get("rejection") or {}).get("explanation") or ""))
        )
        qualities = [float(r.get("trust") or r.get("readiness") or 0) for r in rows]
        avg = round(sum(qualities) / len(qualities), 2) if qualities else 0.0

        best_name = UNKNOWN
        best_potential = UNKNOWN
        best_missing = UNKNOWN
        best_score = -1.0
        for r in rows:
            if r.get("verdict") == GtVerdict.REJECTED.value:
                continue
            score = float(r.get("trust") or 0)
            if score > best_score:
                best_score = score
                best_name = str(r.get("company_name") or UNKNOWN)
                card = r.get("card") or {}
                best_potential = str(card.get("recommended_service") or ((r.get("founder_item") or {}).get("estimated_deal")) or UNKNOWN)
                missing = ((r.get("questions") or {}).get("missing") or [])
                best_missing = ", ".join(missing) if missing else "None"

        return DailyImprovementReport(
            date=date or datetime.now(UTC).date().isoformat(),
            collected=n,
            rejected=rejected,
            passed=passed,
            sales_ready=sales,
            enterprise=enterprise,
            emails_recovered=emails,
            phones_recovered=phones,
            fake_removed=fake,
            duplicates_merged=duplicates_merged,
            average_quality=avg,
            todays_best_company=best_name,
            todays_best_potential=best_potential,
            todays_best_missing=best_missing,
            scoring_version="alpha-plus-v1",
            evidence=[f"collected:{n}", f"passed:{passed}", f"avg_quality:{avg}"],
        )
