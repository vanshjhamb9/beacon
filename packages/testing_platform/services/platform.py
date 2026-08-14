from __future__ import annotations

from typing import Any

from testing_platform.e2e.sandbox_pipeline import SandboxPipelineE2E
from testing_platform.health.system import SystemHealthBuilder
from testing_platform.monitors.probes import ProbeCatalog


class TestingPlatformService:
    def __init__(self) -> None:
        self.health_builder = SystemHealthBuilder()
        self.probes = ProbeCatalog()
        self.e2e = SandboxPipelineE2E()

    def system_health(self, live_probes: dict[str, dict[str, Any]] | None = None, *, mode: str = "sandbox"):
        probes = self.probes.defaults(mode=mode)
        if live_probes:
            probes.update(live_probes)
        return self.health_builder.build(probes, mode=mode)

    def run_sandbox_e2e(self):
        return self.e2e.run()
