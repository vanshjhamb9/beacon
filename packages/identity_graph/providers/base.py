"""IdentityProvider protocol — evidence only, never writes companies."""

from __future__ import annotations

from typing import Any, Protocol

from identity_graph.models.types import IdentityEvidence


class IdentityProvider(Protocol):
    name: str

    def collect(self, payload: dict[str, Any]) -> list[IdentityEvidence]:
        """Return attributed evidence. Never invent values."""
        ...
