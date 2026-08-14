"""Evidence engine — every field is attributed IdentityEvidence."""

from __future__ import annotations

from typing import Any

from identity_graph.models.types import IdentityEvidence
from identity_graph.providers.engines import DEFAULT_PROVIDERS


class EvidenceEngine:
    def __init__(self, providers: tuple | list | None = None) -> None:
        self.providers = list(providers or DEFAULT_PROVIDERS)

    def collect(self, payload: dict[str, Any]) -> list[IdentityEvidence]:
        items: list[IdentityEvidence] = []
        seen: set[str] = set()
        for provider in self.providers:
            for ev in provider.collect(payload):
                key = f"{ev.field}|{ev.value}|{ev.source}"
                if key in seen:
                    continue
                seen.add(key)
                items.append(ev)
        return items

    def best(self, items: list[IdentityEvidence], field: str) -> IdentityEvidence | None:
        matches = [e for e in items if e.field == field]
        if not matches:
            return None
        return sorted(matches, key=lambda e: e.confidence, reverse=True)[0]
