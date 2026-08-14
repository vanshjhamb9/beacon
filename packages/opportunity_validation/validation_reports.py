"""Validation reports — generates comprehensive validation reports."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class ValidationReports:
    """Generates comprehensive validation reports."""

    def __init__(self):
        self._reports: dict[str, dict[str, Any]] = {}

    def generate_report(
        self,
        opportunity_id: str,
        company_name: str,
        validation_outcome: dict[str, Any],
        timeline: list[dict[str, Any]],
        signal_trace: dict[str, Any] | None,
        company_trace: dict[str, Any] | None,
        connector_trace: dict[str, Any] | None,
        staleness: dict[str, Any],
        buying_reason: dict[str, Any],
        human_review: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Generate comprehensive validation report."""
        report = {
            "report_id": str(uuid4()),
            "opportunity_id": opportunity_id,
            "company_name": company_name,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "validation": validation_outcome,
            "timeline": timeline,
            "timeline_length": len(timeline),
            "signal_trace": signal_trace,
            "company_trace": company_trace,
            "connector_trace": connector_trace,
            "staleness": staleness,
            "buying_reason": buying_reason,
            "human_review": human_review,
            "summary": self._build_summary(
                validation_outcome, timeline, staleness, buying_reason
            ),
        }

        self._reports[opportunity_id] = report
        return report

    def get_report(self, opportunity_id: str) -> dict[str, Any] | None:
        """Get report for opportunity."""
        return self._reports.get(opportunity_id)

    def get_all_reports(self) -> list[dict[str, Any]]:
        """Get all reports."""
        return list(self._reports.values())

    def get_reports_by_decision(self, decision: str) -> list[dict[str, Any]]:
        """Get all reports with specific decision."""
        return [
            report for report in self._reports.values()
            if report.get("validation", {}).get("decision") == decision
        ]

    def get_statistics(self) -> dict[str, Any]:
        """Get report statistics."""
        total = len(self._reports)
        decisions = {}
        for report in self._reports.values():
            decision = report.get("validation", {}).get("decision", "unknown")
            decisions[decision] = decisions.get(decision, 0) + 1

        return {
            "total_reports": total,
            "by_decision": decisions,
        }

    def _build_summary(
        self,
        validation: dict[str, Any],
        timeline: list[dict[str, Any]],
        staleness: dict[str, Any],
        buying_reason: dict[str, Any],
    ) -> dict[str, Any]:
        """Build human-readable summary."""
        decision = validation.get("decision", "unknown")
        reasons = validation.get("reasons", [])
        staleness_status = staleness.get("status", "unknown")
        why_now = buying_reason.get("why_now", "unknown")
        would_contact = buying_reason.get("would_contact", False)

        summary_parts = []
        summary_parts.append(f"Decision: {decision.upper()}")
        if reasons:
            summary_parts.append(f"Reasons: {'; '.join(reasons[:3])}")
        summary_parts.append(f"Staleness: {staleness_status}")
        summary_parts.append(f"Why Now: {why_now}")
        summary_parts.append(f"Would SDR Contact: {'YES' if would_contact else 'NO'}")
        summary_parts.append(f"Timeline Events: {len(timeline)}")

        return {
            "text": " | ".join(summary_parts),
            "decision": decision,
            "staleness": staleness_status,
            "why_now": why_now,
            "would_contact": would_contact,
            "timeline_events": len(timeline),
        }

    def clear(self):
        """Clear all reports (for testing)."""
        self._reports.clear()
