"""CLR v1 deterministic param matrix — 900+ cases."""

from __future__ import annotations

import time

import pytest

from revenue_validation.attribution.engine import AttributionEngine
from revenue_validation.briefs.engine import DailyBriefEngine, WeeklyReviewEngine
from revenue_validation.health.engine import ProductionHealthEngine
from revenue_validation.learning.engine import LearningEngine
from revenue_validation.models.types import OutcomeType
from revenue_validation.outcomes.engine import OutcomeEngine
from revenue_validation.prediction.engine import PredictionValidationEngine

OUTCOMES = list(OutcomeType)
TRI = ("YES", "PARTIAL", "NO", "UNKNOWN")
BINARY = ("YES", "NO", "UNKNOWN")
INDUSTRIES = ("Software", "Payments", "Biotechnology", "Gaming", "Healthcare")
SERVICES = (
    "AI Recruiting Automation",
    "AI Customer Support Automation",
    "AI Ops Automation",
    "AI Product Analytics Automation",
)
CONNECTORS = ("yc", "app_store", "product_hunt", "github_trending")

CASES: list[tuple] = []
for i in range(680):
    outcome = OUTCOMES[i % len(OUTCOMES)]
    industry = INDUSTRIES[i % len(INDUSTRIES)]
    service = SERVICES[i % len(SERVICES)]
    connector = CONNECTORS[i % len(CONNECTORS)]
    CASES.append((i, outcome.value, industry, service, connector, f"Co{i}"))

assert len(CASES) >= 680


@pytest.mark.parametrize("i,outcome,industry,service,connector,name", CASES)
def test_clr_pipeline_param(i, outcome, industry, service, connector, name):
    oe = OutcomeEngine()
    ev = oe.transition(
        company_id=f"c-{i}",
        outreach_record_id=f"r-{i}",
        outcome=outcome,
        previous_state="READY" if outcome != "READY" else None,
        actor="founder",
        source="test",
        notes=f"case-{i}",
    )
    assert ev.outcome.value == outcome
    assert ev.company_id == f"c-{i}"
    assert ev.timestamp

    brief = {
        "recommended_service": service,
        "industry": industry,
        "source": connector,
        "decision_maker": f"Person {i} (CEO)",
        "why_now": f"Why {i}",
        "business_email": f"sales@{name.lower()}.com",
        "revenue_ready_score": 90 + (i % 10),
    }
    records = [
        {
            "company_id": f"c-{i}",
            "company": name,
            "status": "CONTACTED" if outcome != "READY" else "READY",
            "brief": brief,
            "pipeline_value": 5000 + i,
            "payload": {"source": connector},
        }
    ]
    outcomes = [
        {
            "company_id": f"c-{i}",
            "outcome": outcome,
            "timestamp": ev.timestamp,
            "new_state": outcome,
        }
    ]
    daily = DailyBriefEngine().build(records=records, outcomes=outcomes)
    assert "contact_first" in daily
    assert len(daily["todays_priority"]) >= 1 or outcome in {"WON", "LOST"}

    pred = PredictionValidationEngine().record(
        company_id=f"c-{i}",
        company=name,
        interested=TRI[i % len(TRI)],
        decision_maker_correct=TRI[(i + 1) % len(TRI)],
        why_now_accurate=TRI[(i + 2) % len(TRI)],
        service_accepted=TRI[(i + 3) % len(TRI)],
        confidence_realistic=BINARY[i % len(BINARY)],
    )
    acc = PredictionValidationEngine().accuracy([pred.model_dump()])
    assert acc["n"] == 1

    if outcome == "WON":
        won = AttributionEngine().build_won(
            company=name,
            company_id=f"c-{i}",
            brief=brief,
            amount=1000 + i,
            close_date="2026-07-25",
            sales_cycle_days=float(i % 30),
            source_connector=connector,
        )
        agg = AttributionEngine().aggregates(
            [{**won.model_dump(), "industry": industry, "decision_maker_role": "CEO"}]
        )
        assert agg["total_revenue"] == 1000 + i
    else:
        agg = AttributionEngine().aggregates([])
        assert agg["total_revenue"] == 0

    learn = LearningEngine().observe(
        records=records, outcomes=outcomes, objections=[], attribution=agg
    )
    assert "best_industries" in learn
    assert "Never" in learn["note"] or "never" in learn["note"].lower() or "Analytics" in learn["note"]


PRED_CASES = [(a, b, c, d, e) for a in TRI for b in TRI for c in TRI for d in ("YES", "NO") for e in BINARY]
assert len(PRED_CASES) >= 200


@pytest.mark.parametrize("interested,dm,why,service,conf", PRED_CASES)
def test_prediction_combos(interested, dm, why, service, conf):
    pv = PredictionValidationEngine().record(
        company_id="x",
        company="X",
        interested=interested,
        decision_maker_correct=dm,
        why_now_accurate=why,
        service_accepted=service if service in TRI else "UNKNOWN",
        confidence_realistic=conf,
    )
    assert pv.interested.value == interested
    acc = PredictionValidationEngine().accuracy([pv.model_dump()])
    assert 0 <= acc["prediction_accuracy"] <= 100


HEALTH_CASES = [(rr, ct, rp, mt, wn) for rr in (0, 5, 10, 20) for ct in (0, 3, 10) for rp in (0, 1, 5) for mt in (0, 1, 3) for wn in (0, 1)]
# 4*3*3*3*2 = 216


@pytest.mark.parametrize("rr,ct,rp,mt,wn", HEALTH_CASES)
def test_health_matrix(rr, ct, rp, mt, wn):
    health = ProductionHealthEngine().evaluate(
        {
            "revenue_ready": rr,
            "contacted": ct,
            "replies": rp,
            "meetings": mt,
            "won": wn,
            "revenue": 4800 if wn else 0,
            "duplicate_pct": 0,
            "fabricated_data": 0,
            "prediction_accuracy": 0,
            "decision_maker_accuracy": 0,
            "revenue_attribution_coverage": 100 if wn == 0 else 100,
        }
    )
    assert len(health) >= 10
    assert all(h["tone"] in {"GREEN", "YELLOW", "RED"} for h in health)
    fab = next(h for h in health if h["metric"] == "Fabricated Data")
    assert fab["tone"] == "GREEN"


def test_weekly_review_shape():
    review = WeeklyReviewEngine().build(
        records=[
            {
                "company_id": "1",
                "company": "A",
                "status": "REPLIED",
                "brief": {
                    "industry": "Software",
                    "recommended_service": "AI Recruiting Automation",
                    "why_now": "YC",
                    "decision_maker": "Ada (CEO)",
                },
            }
        ],
        outcomes=[],
        revenue_rows=[],
        predictions=[],
        objections=[{"label": "No Reply"}],
        attribution={"largest_deal": 0, "revenue_per_connector": {"yc": 0}},
    )
    assert "best_industries" in review
    assert "biggest_objections" in review


def test_performance_1000_companies_under_5s():
    records = []
    outcomes = []
    for i in range(1000):
        records.append(
            {
                "company_id": f"c{i}",
                "company": f"Co{i}",
                "status": "READY" if i % 5 else "CONTACTED",
                "brief": {
                    "industry": INDUSTRIES[i % 5],
                    "recommended_service": SERVICES[i % 4],
                    "why_now": f"signal-{i}",
                    "decision_maker": f"P{i} (CEO)",
                    "business_email": f"sales@co{i}.com",
                    "revenue_ready_score": 90,
                },
                "pipeline_value": 5000,
            }
        )
        outcomes.append({"company_id": f"c{i}", "outcome": "READY", "timestamp": "2026-07-25T00:00:00+00:00"})
    t0 = time.perf_counter()
    brief = DailyBriefEngine().build(records=records, outcomes=outcomes)
    learn = LearningEngine().observe(records=records, outcomes=outcomes, objections=[], attribution={})
    health = ProductionHealthEngine().evaluate(
        {
            "revenue_ready": 1000,
            "contacted": 200,
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
    elapsed = time.perf_counter() - t0
    assert brief["contact_first"]["company"]
    assert learn["best_industries"]
    assert health
    assert elapsed < 5.0, f"took {elapsed:.2f}s"
