from sqlalchemy.dialects import postgresql

from app.models.quality import QualityReport
from app.models.raw_event import RawEvent, RawEventStatus


def test_intelligence_gate_requires_accepted_quality_report() -> None:
    accepted_quality_report = QualityReport.raw_event_id == RawEvent.id
    accepted_decision = QualityReport.decision == "accept"
    raw_event_received = RawEvent.status == RawEventStatus.RECEIVED

    query_text = str(
        (raw_event_received & accepted_quality_report & accepted_decision).compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )

    assert "raw_events.status = 'RECEIVED'" in query_text
    assert "quality_reports.raw_event_id = raw_events.id" in query_text
    assert "quality_reports.decision = 'accept'" in query_text
