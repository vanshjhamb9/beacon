from __future__ import annotations

from typing import Any


class ProbeCatalog:
    """Normalize health probes for API/worker/dashboard surfaces."""

    EXPECTED = [
        "api",
        "workers",
        "database",
        "redis",
        "queues",
        "llm",
        "campaigns",
        "communication",
        "dashboard",
        "webhooks",
        "providers",
        "collectors",
        "pipeline",
    ]

    def defaults(self, *, mode: str = "sandbox") -> dict[str, dict[str, Any]]:
        base = {name: {"status": "ok", "score": 95.0, "latency_ms": 1.0} for name in self.EXPECTED}
        base["communication"] = {
            "status": "ok",
            "score": 100.0 if mode == "sandbox" else 80.0,
            "latency_ms": 1.0,
            "mode": mode,
            "production_send": mode == "production",
        }
        base["queues"] = {"status": "ok", "score": 95.0, "latency_ms": 1.0, "depths": {}}
        base["llm"] = {"status": "ok", "score": 90.0, "grounding": True, "hallucination_checks": True}
        return base
