from uuid import uuid4

import pytest

from revenue_operations.alerts.engine import SmartAlertEngine
from revenue_operations.models.types import AlertLifecycle, OpportunitySignal, RevenueOperationsInput


def _input(**kwargs: object) -> RevenueOperationsInput:
    return RevenueOperationsInput(
        opportunities=[
            OpportunitySignal(
                company_id=uuid4(),
                company_name="Alert Co",
                probability=85,
                pipeline_value=50000,
                reply_waiting=True,
                days_in_stage=3,
                **{k: v for k, v in kwargs.items() if k != "existing_alert_keys"},
            )
        ],
        existing_alert_keys=list(kwargs.get("existing_alert_keys") or []),
    )


def test_lifecycle_path_new_to_archived() -> None:
    eng = SmartAlertEngine()
    state = AlertLifecycle.NEW
    state = eng.transition(state, AlertLifecycle.VIEWED)
    state = eng.transition(state, AlertLifecycle.RESOLVED)
    state = eng.transition(state, AlertLifecycle.ARCHIVED)
    assert state == AlertLifecycle.ARCHIVED


def test_lifecycle_dismiss_path() -> None:
    eng = SmartAlertEngine()
    state = eng.transition(AlertLifecycle.NEW, AlertLifecycle.DISMISSED)
    state = eng.transition(state, AlertLifecycle.ARCHIVED)
    assert state == AlertLifecycle.ARCHIVED


def test_invalid_lifecycle_jumps() -> None:
    eng = SmartAlertEngine()
    with pytest.raises(ValueError):
        eng.transition(AlertLifecycle.NEW, AlertLifecycle.RESOLVED)
    with pytest.raises(ValueError):
        eng.transition(AlertLifecycle.DISMISSED, AlertLifecycle.VIEWED)


def test_no_duplicate_alerts_same_dedupe() -> None:
    eng = SmartAlertEngine()
    first = eng.detect(_input())
    assert first
    second = eng.detect(_input(existing_alert_keys=[a.dedupe_key for a in first]))
    overlap = {a.dedupe_key for a in first} & {a.dedupe_key for a in second}
    assert not overlap
