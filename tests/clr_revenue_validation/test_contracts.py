"""CLR v1 contract tests."""

from __future__ import annotations

from pathlib import Path

from revenue_validation import VERSION, OutcomeType
from revenue_validation.attribution.engine import AttributionEngine
from revenue_validation.briefs.engine import DailyBriefEngine
from revenue_validation.health.engine import ProductionHealthEngine
from revenue_validation.learning.engine import LearningEngine
from revenue_validation.outcomes.engine import OutcomeEngine
from revenue_validation.prediction.engine import PredictionValidationEngine


def test_version():
    assert VERSION == "clr-v1"


def test_outcome_enum_complete():
    required = {
        "READY",
        "CONTACTED",
        "EMAIL_SENT",
        "OPENED",
        "CLICKED",
        "REPLIED",
        "POSITIVE_REPLY",
        "NEGATIVE_REPLY",
        "MEETING_BOOKED",
        "MEETING_COMPLETED",
        "PROPOSAL_SENT",
        "NEGOTIATION",
        "WON",
        "LOST",
        "NO_RESPONSE",
        "FOLLOW_UP_REQUIRED",
        "FOLLOW_UP_SENT",
    }
    assert required <= {o.value for o in OutcomeType}


def test_outcome_append_fields():
    ev = OutcomeEngine().transition(
        company_id="c1",
        outreach_record_id="r1",
        outcome="CONTACTED",
        previous_state="READY",
        notes="hi",
    )
    assert ev.previous_state == "READY"
    assert ev.new_state == "CONTACTED"
    assert ev.timestamp
    assert ev.actor == "founder"


def test_attribution_zero_without_wins():
    agg = AttributionEngine().aggregates([])
    assert agg["total_revenue"] == 0
    assert agg["deal_count"] == 0


def test_attribution_won():
    row = AttributionEngine().build_won(
        company="Acme",
        company_id="1",
        brief={"recommended_service": "AI Recruiting Automation", "industry": "Software"},
        amount=4800,
        close_date="2026-07-25",
        sales_cycle_days=7,
    )
    agg = AttributionEngine().aggregates([row.model_dump()])
    assert agg["total_revenue"] == 4800
    assert agg["largest_deal"] == 4800


def test_prediction_accuracy_unknown():
    acc = PredictionValidationEngine().accuracy(
        [{"interested": "UNKNOWN", "decision_maker_correct": "UNKNOWN"}]
    )
    assert acc["coverage"] == 0.0


def test_prediction_accuracy_yes():
    acc = PredictionValidationEngine().accuracy(
        [
            {
                "interested": "YES",
                "decision_maker_correct": "YES",
                "why_now_accurate": "PARTIAL",
                "service_accepted": "NO",
                "confidence_realistic": "YES",
            }
        ]
    )
    assert acc["prediction_accuracy"] == 100.0
    assert acc["why_now_accuracy"] == 50.0


def test_daily_brief_contact_first():
    brief = DailyBriefEngine().build(
        records=[
            {
                "company_id": "1",
                "company": "Amplitude",
                "status": "READY",
                "brief": {
                    "decision_maker": "Spenser Skates (Founder / CEO)",
                    "business_email": "sales@amplitude.com",
                    "why_now": "YC growth",
                    "revenue_ready_score": 99,
                },
            }
        ],
        outcomes=[],
    )
    assert brief["contact_first"]["company"] == "Amplitude"
    assert "todays_priority" in brief


def test_health_tones():
    health = ProductionHealthEngine().evaluate(
        {
            "revenue_ready": 10,
            "contacted": 10,
            "replies": 0,
            "meetings": 0,
            "won": 0,
            "revenue": 0,
            "duplicate_pct": 0,
            "fabricated_data": 0,
            "prediction_accuracy": 0,
            "decision_maker_accuracy": 0,
            "revenue_attribution_coverage": 100,
        }
    )
    tones = {h["metric"]: h["tone"] for h in health}
    assert tones["Fabricated Data"] == "GREEN"
    assert tones["Revenue Ready"] == "GREEN"


def test_learning_never_mutates_input():
    records = [{"company": "X", "status": "READY", "brief": {"industry": "Software"}}]
    before = str(records)
    LearningEngine().observe(records=records, outcomes=[], objections=[], attribution={})
    assert str(records) == before


def test_migration_file_exists():
    root = Path(__file__).resolve().parents[2]
    path = root / "apps" / "api" / "alembic" / "versions" / "20260725_0046_create_clr_v1_tables.py"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "clr_outcome_events" in text
    assert "clr_revenue_events" in text
    assert 'revision = "20260725_0046"' in text
