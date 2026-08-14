"""IdentityCoverageProvider — evidence only."""

from __future__ import annotations

from typing import Any, Protocol

from identity_coverage.models.types import CoverageEvidence


class IdentityCoverageProvider(Protocol):
    name: str
    priority: int

    def collect(self, payload: dict[str, Any]) -> list[CoverageEvidence]:
        ...
