import pytest

from revenue_optimization import RevenueOptimizationPipeline, RevenueOptimizationService
from revenue_optimization.email_performance.engine import EmailPerformanceEngine
from revenue_optimization.models.types import OutreachEvent


@pytest.mark.parametrize("i", range(50))
def test_subject_matrix(make_event, i: int) -> None:
    events = [
        make_event(subject=f"Line {i}", opened=True, replied=i % 2 == 0, closed_won=i % 5 == 0, deal_value=5000 if i % 5 == 0 else 0),
        make_event(subject=f"Alt {i % 3}", opened=False, replied=False, closed_won=False, deal_value=0, reply_text=""),
    ]
    d = RevenueOptimizationPipeline().process(
        __import__("revenue_optimization.models.types", fromlist=["ROIPInput"]).ROIPInput(events=events)
    )
    assert d.subjects
    assert d.email_metrics.confidence >= 0


@pytest.mark.parametrize(
    "device,country",
    [("desktop", "US"), ("mobile", "IN"), ("tablet", "GB"), ("desktop", "AE"), ("mobile", "SG")],
)
def test_email_device_country(make_event, device: str, country: str) -> None:
    m = EmailPerformanceEngine().analyze([make_event(open_device=device, open_country=country, opened=True)])
    assert m.open_devices.get(device, 0) >= 1
    assert m.open_countries.get(country, 0) >= 1


def test_service_search_offer_filter(make_input) -> None:
    decision = RevenueOptimizationService().evaluate(make_input(5, offer="CRM"))
    found = RevenueOptimizationService().search(decision, filters={"offer": "CRM"})
    assert all(o["offer"] == "CRM" for o in found["offers"])


def test_service_search_reply_type(make_input) -> None:
    decision = RevenueOptimizationService().evaluate(make_input(4, replied=True, reply_text="interested"))
    found = RevenueOptimizationService().search(decision, filters={"reply_type": "interested"})
    assert all(r["category"] == "interested" for r in found["replies"])


def test_frozen_events_immutable(make_event) -> None:
    e = make_event()
    with pytest.raises(Exception):
        e.opened = False  # type: ignore[misc]
