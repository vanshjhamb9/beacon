from __future__ import annotations

from outcome_intelligence.models.types import OutcomeLifecycle

_STAGE_ORDER: tuple[OutcomeLifecycle, ...] = (
    OutcomeLifecycle.NEW,
    OutcomeLifecycle.REVIEWED,
    OutcomeLifecycle.CONTACTED,
    OutcomeLifecycle.REPLIED,
    OutcomeLifecycle.MEETING_SCHEDULED,
    OutcomeLifecycle.QUALIFIED,
    OutcomeLifecycle.PROPOSAL_SENT,
    OutcomeLifecycle.NEGOTIATION,
    OutcomeLifecycle.WON,
    OutcomeLifecycle.LOST,
    OutcomeLifecycle.ARCHIVED,
)

_OUTCOME_SCORE: dict[str, float] = {
    OutcomeLifecycle.NEW.value: 5.0,
    OutcomeLifecycle.REVIEWED.value: 15.0,
    OutcomeLifecycle.CONTACTED.value: 30.0,
    OutcomeLifecycle.REPLIED.value: 45.0,
    OutcomeLifecycle.MEETING_SCHEDULED.value: 60.0,
    OutcomeLifecycle.QUALIFIED.value: 70.0,
    OutcomeLifecycle.PROPOSAL_SENT.value: 80.0,
    OutcomeLifecycle.NEGOTIATION.value: 85.0,
    OutcomeLifecycle.WON.value: 100.0,
    OutcomeLifecycle.LOST.value: 0.0,
    OutcomeLifecycle.ARCHIVED.value: 0.0,
}


def stage_order() -> tuple[OutcomeLifecycle, ...]:
    return _STAGE_ORDER


def outcome_score(stage: str | OutcomeLifecycle) -> float:
    key = stage.value if isinstance(stage, OutcomeLifecycle) else str(stage)
    return float(_OUTCOME_SCORE.get(key, 0.0))


def is_terminal(stage: str | OutcomeLifecycle) -> bool:
    key = stage.value if isinstance(stage, OutcomeLifecycle) else str(stage)
    return key in {
        OutcomeLifecycle.WON.value,
        OutcomeLifecycle.LOST.value,
        OutcomeLifecycle.ARCHIVED.value,
    }


def normalize_stage(value: str) -> OutcomeLifecycle:
    cleaned = value.strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "meeting": OutcomeLifecycle.MEETING_SCHEDULED,
        "meeting_booked": OutcomeLifecycle.MEETING_SCHEDULED,
        "proposal": OutcomeLifecycle.PROPOSAL_SENT,
        "closed_won": OutcomeLifecycle.WON,
        "closed_lost": OutcomeLifecycle.LOST,
    }
    if cleaned in aliases:
        return aliases[cleaned]
    return OutcomeLifecycle(cleaned)
