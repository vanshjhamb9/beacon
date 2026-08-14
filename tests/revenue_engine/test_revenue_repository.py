from inspect import signature

from app.repositories.revenue import RevenueRepository
from app.services.revenue import RevenueService
from revenue_engine.repository.protocols import RevenueInputRepository


def test_revenue_repository_implements_protocol_methods() -> None:
    required = {"pending_opportunity_inputs", "list_enabled_services", "store_recommendation"}
    assert required.issubset(set(dir(RevenueRepository)))
    assert callable(RevenueRepository.pending_opportunity_inputs)
    assert callable(RevenueRepository.store_recommendation)
    assert set(signature(RevenueInputRepository.pending_opportunity_inputs).parameters) == {
        "self",
        "limit",
    }


def test_revenue_service_exposes_process_and_read_apis() -> None:
    methods = {
        "process_pending",
        "list_opportunities",
        "company_revenue",
        "company_playbook",
        "statistics",
        "ensure_catalog_seeded",
    }
    assert methods.issubset(set(dir(RevenueService)))
