from uuid import uuid4

from autonomous_sales_agent.models.types import AutonomousSalesAgentInput
from autonomous_sales_agent.timeline.engine import RelationshipTimelineEngine


def test_timeline_seeds_append() -> None:
    events = RelationshipTimelineEngine().build(
        AutonomousSalesAgentInput(
            company_id=uuid4(),
            company_name="Seed Co",
            timeline_seeds=[{"event_type": "custom", "title": "Custom", "detail": "x", "actor": "ops"}],
        )
    )
    assert any(e.event_type == "custom" and e.actor == "ops" for e in events)


def test_timeline_never_mutates_previous_list() -> None:
    eng = RelationshipTimelineEngine()
    item = AutonomousSalesAgentInput(company_id=uuid4(), company_name="T", email_sent=True)
    a = eng.build(item)
    b = eng.build(item)
    assert len(a) == len(b)
    assert a is not b
