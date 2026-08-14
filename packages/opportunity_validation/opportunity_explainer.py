"""Opportunity explainer — explains why every company appears in Beacon.

Every card in Beacon must expose:
    Why am I seeing this company?
    Collected by
    Evidence
    Detected
    Freshness
    Buying Signal
    ICP
    Revenue Score
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class OpportunityExplainer:
    """Explains why every company appears in Beacon."""

    def explain(
        self,
        opportunity_id: str,
        company_name: str,
        website: str,
        connector: str,
        evidence: dict[str, Any],
        detection_timestamp: datetime,
        freshness: str,
        buying_signal: str,
        buying_signal_strength: str,
        icp_match: bool,
        icp_score: float,
        quality_score: int,
        timeline_events: list[dict[str, Any]],
        why_now: str,
        validation_decision: str,
    ) -> dict[str, Any]:
        """Generate explanation for opportunity."""
        explanation = {
            "opportunity_id": opportunity_id,
            "company_name": company_name,
            "website": website,
            "why_am_i_seeing_this": self._build_why_summary(
                connector, evidence, buying_signal, freshness
            ),
            "collected_by": connector,
            "evidence": self._format_evidence(evidence),
            "detected": detection_timestamp.isoformat() if isinstance(detection_timestamp, datetime) else str(detection_timestamp),
            "freshness": freshness,
            "buying_signal": buying_signal,
            "buying_signal_strength": buying_signal_strength,
            "icp_match": icp_match,
            "icp_score": icp_score,
            "quality_score": quality_score,
            "timeline_events": timeline_events,
            "timeline_length": len(timeline_events),
            "why_now": why_now,
            "validation_decision": validation_decision,
            "human_readable": self._build_human_readable(
                company_name, connector, evidence, buying_signal,
                freshness, icp_match, quality_score, why_now,
                validation_decision, timeline_events
            ),
        }

        return explanation

    def _build_why_summary(
        self,
        connector: str,
        evidence: dict[str, Any],
        buying_signal: str,
        freshness: str,
    ) -> str:
        """Build why summary."""
        parts = []
        parts.append(f"Discovered by {connector}")
        if evidence:
            evidence_keys = list(evidence.keys())[:3]
            parts.append(f"Evidence: {', '.join(evidence_keys)}")
        parts.append(f"Signal: {buying_signal}")
        parts.append(f"Freshness: {freshness}")
        return "; ".join(parts)

    def _format_evidence(self, evidence: dict[str, Any]) -> list[dict[str, Any]]:
        """Format evidence for display."""
        formatted = []
        for key, value in evidence.items():
            formatted.append({
                "type": key,
                "value": str(value),
            })
        return formatted

    def _build_human_readable(
        self,
        company_name: str,
        connector: str,
        evidence: dict[str, Any],
        buying_signal: str,
        freshness: str,
        icp_match: bool,
        quality_score: int,
        why_now: str,
        validation_decision: str,
        timeline_events: list[dict[str, Any]],
    ) -> str:
        """Build human-readable explanation."""
        parts = []

        # Why am I seeing this?
        parts.append(f"You are seeing {company_name} because {connector} discovered them.")

        # Evidence
        if evidence:
            evidence_desc = list(evidence.values())[:2]
            parts.append(f"Evidence: {'; '.join(str(e) for e in evidence_desc)}")

        # Signal
        parts.append(f"They have a {buying_signal} signal.")

        # Freshness
        parts.append(f"The signal is {freshness}.")

        # ICP
        if icp_match:
            parts.append("They match your ICP.")
        else:
            parts.append("They do not match your ICP.")

        # Quality
        parts.append(f"Quality score: {quality_score}/100.")

        # Why now
        if why_now and why_now != "unknown":
            parts.append(f"Why now: {why_now}.")

        # Timeline
        if timeline_events:
            parts.append(f"Timeline has {len(timeline_events)} events.")

        # Decision
        parts.append(f"Validation: {validation_decision.upper()}.")

        return " ".join(parts)

    def get_card_data(
        self,
        opportunity_id: str,
        company_name: str,
        website: str,
        connector: str,
        evidence: dict[str, Any],
        detection_timestamp: datetime,
        freshness: str,
        buying_signal: str,
        icp_match: bool,
        quality_score: int,
    ) -> dict[str, Any]:
        """Get data for Beacon card display."""
        return {
            "title": company_name,
            "subtitle": website,
            "badge": connector,
            "freshness": freshness,
            "buying_signal": buying_signal,
            "icp_match": "Yes" if icp_match else "No",
            "quality_score": f"{quality_score}/100",
            "detected": detection_timestamp.isoformat() if isinstance(detection_timestamp, datetime) else str(detection_timestamp),
        }
