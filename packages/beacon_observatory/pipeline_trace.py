"""Pipeline Trace — traces opportunity through entire pipeline."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class TraceStep:
    """Single pipeline trace step."""

    def __init__(self, data: dict[str, Any]):
        self.stage: str = data.get("stage", "unknown")
        self.timestamp: datetime = data.get("timestamp", datetime.now(timezone.utc))
        self.duration_seconds: float = data.get("duration_seconds", 0.0)
        self.decision: str = data.get("decision", "unknown")
        self.evidence: dict[str, Any] = data.get("evidence", {})
        self.worker: str = data.get("worker", "unknown")

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "timestamp": self.timestamp.isoformat(),
            "duration_seconds": self.duration_seconds,
            "decision": self.decision,
            "evidence": self.evidence,
            "worker": self.worker,
        }


class PipelineTrace:
    """Traces opportunity through entire pipeline."""

    def __init__(self):
        self._traces: dict[str, list[TraceStep]] = {}

    def add_step(
        self,
        opportunity_id: str,
        stage: str,
        decision: str = "unknown",
        evidence: dict[str, Any] | None = None,
        worker: str = "system",
        duration: float = 0.0,
    ) -> TraceStep:
        """Add trace step for opportunity."""
        step = TraceStep({
            "stage": stage,
            "decision": decision,
            "evidence": evidence or {},
            "worker": worker,
            "duration_seconds": duration,
        })

        if opportunity_id not in self._traces:
            self._traces[opportunity_id] = []
        self._traces[opportunity_id].append(step)

        return step

    def get_trace(self, opportunity_id: str) -> list[TraceStep]:
        """Get full trace for opportunity."""
        return self._traces.get(opportunity_id, [])

    def get_all_traces(self) -> dict[str, list[dict[str, Any]]]:
        """Get all traces."""
        return {
            opp_id: [step.to_dict() for step in steps]
            for opp_id, steps in self._traces.items()
        }

    def get_stages_reached(self, opportunity_id: str) -> list[str]:
        """Get stages reached by opportunity."""
        steps = self._traces.get(opportunity_id, [])
        return [step.stage for step in steps]

    def get_total_duration(self, opportunity_id: str) -> float:
        """Get total duration for opportunity."""
        steps = self._traces.get(opportunity_id, [])
        return sum(step.duration_seconds for step in steps)

    def get_statistics(self) -> dict[str, Any]:
        """Get trace statistics."""
        total_traces = len(self._traces)
        total_steps = sum(len(steps) for steps in self._traces.values())

        stages = {}
        for steps in self._traces.values():
            for step in steps:
                stages[step.stage] = stages.get(step.stage, 0) + 1

        return {
            "total_traces": total_traces,
            "total_steps": total_steps,
            "stages": stages,
        }
