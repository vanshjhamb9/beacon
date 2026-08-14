import time

from revenue_optimization import RevenueOptimizationService
from revenue_optimization.models.types import ROIPInput


def test_1000_campaign_evaluations_under_5_seconds(make_event) -> None:
    service = RevenueOptimizationService()
    items: list[ROIPInput] = []
    for i in range(1000):
        events = [
            make_event(
                event_id=f"perf-{i}-{j}",
                campaign_id=f"camp-{i}",
                industry=["SaaS", "Healthcare", "Manufacturing", "Construction"][i % 4],
                subject=f"Subject {i % 17}",
                cta=["book_meeting", "ai_audit", "watch_demo"][i % 3],
                offer=["AI Automation", "CRM", "Custom SaaS"][i % 3],
                opened=i % 2 == 0,
                replied=i % 5 == 0,
                closed_won=i % 11 == 0,
                deal_value=15000 if i % 11 == 0 else 0,
            )
            for j in range(2)
        ]
        items.append(ROIPInput(events=events, previous_period_events=events[:1]))
    start = time.perf_counter()
    out = service.evaluate_many(items)
    elapsed = time.perf_counter() - start
    assert len(out) == 1000
    assert elapsed < 5.0, f"took {elapsed:.3f}s"


def test_single_eval_fast(make_event) -> None:
    events = [make_event(event_id=f"s{i}") for i in range(50)]
    start = time.perf_counter()
    RevenueOptimizationService().evaluate(ROIPInput(events=events))
    assert time.perf_counter() - start < 1.0
