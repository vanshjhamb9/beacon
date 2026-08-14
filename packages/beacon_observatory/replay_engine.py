"""Replay Engine — replays collector runs for debugging."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class ReplayResult:
    """Single replay result."""

    def __init__(self, data: dict[str, Any]):
        self.id: str = data.get("id", str(uuid4()))
        self.run_id: str = data.get("run_id", "unknown")
        self.connector: str = data.get("connector", "unknown")
        self.stages: list[dict[str, Any]] = data.get("stages", [])
        self.replayed_at: datetime = data.get("replayed_at", datetime.now(timezone.utc))
        self.total_duration: float = data.get("total_duration", 0.0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "run_id": self.run_id,
            "connector": self.connector,
            "stages": self.stages,
            "replayed_at": self.replayed_at.isoformat(),
            "total_duration": self.total_duration,
        }


class ReplayEngine:
    """Replays collector runs for debugging."""

    def __init__(self):
        self._replays: dict[str, ReplayResult] = {}

    def replay_run(
        self,
        run_id: str,
        connector: str,
        stages: list[dict[str, Any]],
    ) -> ReplayResult:
        """Replay a collector run."""
        result = ReplayResult({
            "run_id": run_id,
            "connector": connector,
            "stages": stages,
        })

        self._replays[run_id] = result
        return result

    def get_replay(self, run_id: str) -> ReplayResult | None:
        """Get replay result."""
        return self._replays.get(run_id)

    def get_all_replays(self) -> list[ReplayResult]:
        """Get all replay results."""
        return list(self._replays.values())

    def get_statistics(self) -> dict[str, Any]:
        """Get replay statistics."""
        total = len(self._replays)
        by_connector = {}

        for replay in self._replays.values():
            by_connector[replay.connector] = by_connector.get(replay.connector, 0) + 1

        return {
            "total_replays": total,
            "by_connector": by_connector,
        }
