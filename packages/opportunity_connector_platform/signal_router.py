"""Route validated evidence into the live opportunity discovery pipeline."""

from __future__ import annotations

from opportunity_connector_platform.connector_events import EvidenceEvent, RoutedEvidenceEvent
from opportunity_connector_platform.signal_normalizer import SignalNormalizer
from opportunity_connector_platform.signal_validator import SignalValidator


class SignalRouter:
    """Normalize → validate → route. Deterministic, no AI scoring."""

    def __init__(
        self,
        *,
        normalizer: SignalNormalizer | None = None,
        validator: SignalValidator | None = None,
    ) -> None:
        self.normalizer = normalizer or SignalNormalizer()
        self.validator = validator or SignalValidator()

    def route(self, event: EvidenceEvent) -> RoutedEvidenceEvent:
        normalized = self.normalizer.normalize(event)
        validation = self.validator.validate(normalized)
        return RoutedEvidenceEvent(
            event=normalized,
            accepted=validation.accepted,
            rejection_reason=None if validation.accepted else validation.reason,
        )

    def route_batch(self, events: list[EvidenceEvent]) -> list[RoutedEvidenceEvent]:
        return [self.route(event) for event in events]

    def accepted_count(self, routed: list[RoutedEvidenceEvent]) -> int:
        return sum(1 for r in routed if r.accepted)

    def rejected_count(self, routed: list[RoutedEvidenceEvent]) -> int:
        return sum(1 for r in routed if not r.accepted)

    def rejection_reasons(self, routed: list[RoutedEvidenceEvent]) -> dict[str, int]:
        reasons: dict[str, int] = {}
        for r in routed:
            if not r.accepted and r.rejection_reason:
                reasons[r.rejection_reason] = reasons.get(r.rejection_reason, 0) + 1
        return reasons
