import time
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from outcome_intelligence import OutcomeIntelligencePipeline


def test_outcome_pipeline_latency_budget() -> None:
    pipeline = OutcomeIntelligencePipeline()
    now = datetime.now(UTC)
    records = [
        {
            "opportunity_id": uuid4(),
            "company_id": uuid4(),
            "lifecycle_stage": stage,
            "opportunity_score": 60.0 + (index % 40),
            "recommended_service": "AI Automation" if index % 2 == 0 else "ERP Modernization",
            "buyer_persona": "CTO",
            "industry": "saas",
            "collector": "reddit" if index % 3 else "github",
            "technology": "Python",
            "decision_maker_role": "CTO",
            "revenue": 10000.0 if stage == "won" else None,
            "created_at": now - timedelta(days=40),
            "updated_at": now,
            "close_date": now if stage == "won" else None,
            "contacted_at": now - timedelta(days=20),
        }
        for index, stage in enumerate(
            ["new", "reviewed", "contacted", "replied", "meeting_scheduled", "qualified", "proposal_sent", "won", "lost"]
            * 40
        )
    ]
    started = time.perf_counter()
    for _ in range(10):
        pipeline.build_dashboard(records)
    elapsed_ms = (time.perf_counter() - started) * 1000
    assert elapsed_ms < 2000.0
