from revenue_optimization.models.types import Period
from revenue_optimization.reply_intelligence.engine import RevenueBenchmarkEngine


def test_benchmark_growth_and_decline(make_event) -> None:
    current = [make_event(opened=True, delivered=True) for _ in range(10)]
    previous = [make_event(opened=False, delivered=True, replied=False, reply_text="") for _ in range(10)]
    benches = RevenueBenchmarkEngine().benchmark(current, previous)
    today = next(b for b in benches if b.period == Period.TODAY)
    assert today.growth >= 0
    assert today.open_rate > today.previous_open_rate


def test_benchmark_all_periods(make_input) -> None:
    data = make_input(8)
    benches = RevenueBenchmarkEngine().benchmark(list(data.events), list(data.previous_period_events))
    assert {b.period for b in benches} == set(Period)


def test_benchmark_evidence(make_input) -> None:
    benches = RevenueBenchmarkEngine().benchmark(list(make_input(5).events), [])
    assert all(b.evidence and b.confidence >= 0 for b in benches)
