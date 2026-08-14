from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from opportunity_intelligence.dashboard_service import DashboardService
from opportunity_intelligence.router import build_opportunity_router
from opportunity_intelligence.schemas import OpportunityResponse


class FakeOpportunityService:
    async def list(self, *, limit: int = 50, offset: int = 0) -> dict[str, object]:
        return {"items": [{"id": "1", "opportunity_score": 90}], "count": 1, "limit": limit, "offset": offset}

    async def get(self, opportunity_id: UUID) -> dict[str, object]:
        return {"id": str(opportunity_id), "company_name": "Microsoft"}

    async def top(self, *, limit: int = 25) -> dict[str, object]:
        return {"items": [{"id": "1"}], "count": 1, "limit": limit}

    async def stats(self) -> dict[str, object]:
        return {"top_opportunities": [], "buying_window_counts": {}}

    def config(self) -> dict[str, object]:
        return {"weights": {"intent": 0.18}}

    def signal_types(self) -> dict[str, object]:
        return {"items": ["HIRING"], "count": 1}


def app() -> FastAPI:
    api = FastAPI()
    api.include_router(build_opportunity_router(lambda: FakeOpportunityService()), prefix="/api/v1")
    return api


def test_opportunity_router_read_only_endpoints() -> None:
    client = TestClient(app())
    assert client.get("/api/v1/opportunities").status_code == 200
    assert client.get("/api/v1/opportunities/top").json()["count"] == 1
    assert client.get("/api/v1/opportunities/stats").status_code == 200
    assert client.get("/api/v1/opportunities/config").json()["weights"]["intent"] == 0.18
    assert client.get("/api/v1/opportunities/signal-types").json()["items"] == ["HIRING"]
    assert client.get("/api/v1/opportunities/00000000-0000-4000-8000-000000000001").json()["company_name"] == "Microsoft"


def test_dashboard_service_returns_required_sections() -> None:
    payload = DashboardService().build(
        [
            {
                "company_name": "Microsoft",
                "opportunity_score": 91,
                "confidence": 88,
                "freshness_score": 100,
                "buying_window": "Immediate",
                "signal_category": "HIRING",
                "industry": "Software",
                "country": "US",
                "created_at": datetime(2026, 7, 29, tzinfo=UTC),
                "signal_age_days": 3,
                "evidence_count": 2,
            }
        ]
    )
    assert set(payload) == {
        "top_opportunities",
        "buying_window_counts",
        "signal_distribution",
        "industry_distribution",
        "country_distribution",
        "opportunity_timeline",
        "freshness_distribution",
        "evidence_distribution",
    }
    assert payload["buying_window_counts"]["Immediate"] == 1


def test_opportunity_response_schema_accepts_full_contract() -> None:
    response = OpportunityResponse(
        id="00000000-0000-4000-8000-000000000001",
        company_id="00000000-0000-4000-8000-000000000002",
        company_name="Microsoft",
        signal_type="headcount_growth",
        signal_source="Career Pages",
        signal_category="HIRING",
        signal_title="Hiring 500 AI Engineers",
        signal_timestamp=datetime(2026, 7, 29, tzinfo=UTC),
        signal_age_days=0,
        buying_window="Immediate",
        intent_score=80,
        pain_score=70,
        budget_score=75,
        growth_score=90,
        timing_score=82,
        freshness_score=100,
        evidence_score=91,
        icp_score=88,
        opportunity_score=84,
        confidence=93,
        trust=90,
        created_at=datetime(2026, 7, 29, tzinfo=UTC),
        updated_at=datetime(2026, 7, 29, tzinfo=UTC),
    )
    assert response.company_name == "Microsoft"


def test_migration_is_append_only_and_mentions_requested_revision_conflict() -> None:
    migration = Path(
        "apps/api/alembic/versions/20260728_0050_opportunity_intelligence_core.py"
    ).read_text(encoding="utf-8")
    assert 'revision = "20260728_0050"' in migration
    assert 'down_revision = "20260727_0049"' in migration
    assert "Sprint 36A requested revision 20260727_0049" in migration
    assert "_add_missing" in migration
    for table in ["opportunities", "opportunity_evidence", "opportunity_scores"]:
        assert f'"{table}"' in migration
