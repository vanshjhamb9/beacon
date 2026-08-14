"""Replay engine — replays any opportunity through every engine.

Extremely important.
Ability to replay ANY opportunity through every engine.

Display:
    Connector → DQE → Validation → Opportunity Intelligence → Revenue Ready

Every decision, every score, every rejection, every timestamp, every explanation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class ReplayEngine:
    """Replays any opportunity through every engine."""

    def __init__(self):
        self._replays: dict[str, dict[str, Any]] = {}

    def replay_opportunity(
        self,
        opportunity_id: str,
        company_name: str,
        connector_data: dict[str, Any],
        dqe_data: dict[str, Any],
        validation_data: dict[str, Any],
        opportunity_intelligence_data: dict[str, Any] | None = None,
        revenue_ready_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Replay opportunity through all engines."""
        replay = {
            "replay_id": str(uuid4()),
            "opportunity_id": opportunity_id,
            "company_name": company_name,
            "replayed_at": datetime.now(timezone.utc).isoformat(),
            "stages": {
                "connector": self._build_connector_stage(connector_data),
                "dqe": self._build_dqe_stage(dqe_data),
                "validation": self._build_validation_stage(validation_data),
                "opportunity_intelligence": self._build_opportunity_intelligence_stage(
                    opportunity_intelligence_data
                ),
                "revenue_ready": self._build_revenue_ready_stage(revenue_ready_data),
            },
            "summary": self._build_replay_summary(
                connector_data, dqe_data, validation_data,
                opportunity_intelligence_data, revenue_ready_data
            ),
        }

        self._replays[opportunity_id] = replay
        return replay

    def _build_connector_stage(self, data: dict[str, Any]) -> dict[str, Any]:
        """Build connector stage."""
        return {
            "stage": "connector",
            "connector": data.get("connector", "unknown"),
            "signal_type": data.get("signal_type", "unknown"),
            "signal_source": data.get("signal_source", "unknown"),
            "original_url": data.get("original_url", "unknown"),
            "original_timestamp": data.get("original_timestamp", "unknown"),
            "collection_timestamp": data.get("collection_timestamp", "unknown"),
            "decision": data.get("decision", "collected"),
            "evidence": data.get("evidence", {}),
        }

    def _build_dqe_stage(self, data: dict[str, Any]) -> dict[str, Any]:
        """Build DQE stage."""
        return {
            "stage": "dqe",
            "quality_score": data.get("quality_score", 0),
            "quality_grade": data.get("quality_grade", "unknown"),
            "freshness": data.get("freshness", "unknown"),
            "buying_signal": data.get("buying_signal", "unknown"),
            "icp_match": data.get("icp_match", False),
            "region_match": data.get("region_match", False),
            "industry_match": data.get("industry_match", False),
            "decision": data.get("decision", "unknown"),
            "gates_passed": data.get("gates_passed", []),
            "gates_failed": data.get("gates_failed", []),
            "evidence": data.get("evidence", {}),
        }

    def _build_validation_stage(self, data: dict[str, Any]) -> dict[str, Any]:
        """Build validation stage."""
        return {
            "stage": "validation",
            "decision": data.get("decision", "unknown"),
            "reasons": data.get("reasons", []),
            "evidence": data.get("evidence", {}),
            "root_cause": data.get("root_cause", "unknown"),
            "human_verdict": data.get("human_verdict", "unknown"),
            "timeline_length": data.get("timeline_length", 0),
            "staleness": data.get("staleness", "unknown"),
            "buying_reason": data.get("buying_reason", "unknown"),
        }

    def _build_opportunity_intelligence_stage(
        self, data: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Build opportunity intelligence stage."""
        if data is None:
            return {
                "stage": "opportunity_intelligence",
                "status": "not_processed",
                "decision": "unknown",
            }

        return {
            "stage": "opportunity_intelligence",
            "status": "processed",
            "decision": data.get("decision", "unknown"),
            "score": data.get("score", 0),
            "evidence": data.get("evidence", {}),
        }

    def _build_revenue_ready_stage(
        self, data: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Build revenue ready stage."""
        if data is None:
            return {
                "stage": "revenue_ready",
                "status": "not_reached",
                "decision": "unknown",
            }

        return {
            "stage": "revenue_ready",
            "status": "reached",
            "decision": data.get("decision", "unknown"),
            "score": data.get("score", 0),
            "evidence": data.get("evidence", {}),
        }

    def _build_replay_summary(
        self,
        connector_data: dict[str, Any],
        dqe_data: dict[str, Any],
        validation_data: dict[str, Any],
        opportunity_intelligence_data: dict[str, Any] | None,
        revenue_ready_data: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Build replay summary."""
        stages_completed = ["connector", "dqe", "validation"]
        if opportunity_intelligence_data:
            stages_completed.append("opportunity_intelligence")
        if revenue_ready_data:
            stages_completed.append("revenue_ready")

        final_decision = validation_data.get("decision", "unknown")
        if revenue_ready_data:
            final_decision = "revenue_ready"
        elif opportunity_intelligence_data:
            final_decision = "opportunity_intelligence"

        return {
            "stages_completed": stages_completed,
            "final_decision": final_decision,
            "connector": connector_data.get("connector", "unknown"),
            "quality_score": dqe_data.get("quality_score", 0),
            "validation_decision": validation_data.get("decision", "unknown"),
        }

    def get_replay(self, opportunity_id: str) -> dict[str, Any] | None:
        """Get replay for opportunity."""
        return self._replays.get(opportunity_id)

    def get_all_replays(self) -> list[dict[str, Any]]:
        """Get all replays."""
        return list(self._replays.values())

    def get_statistics(self) -> dict[str, Any]:
        """Get replay statistics."""
        total = len(self._replays)
        decisions = {}
        connectors = {}

        for replay in self._replays.values():
            summary = replay.get("summary", {})
            decision = summary.get("final_decision", "unknown")
            connector = summary.get("connector", "unknown")
            decisions[decision] = decisions.get(decision, 0) + 1
            connectors[connector] = connectors.get(connector, 0) + 1

        return {
            "total_replays": total,
            "by_decision": decisions,
            "by_connector": connectors,
        }

    def clear(self):
        """Clear all replays (for testing)."""
        self._replays.clear()
