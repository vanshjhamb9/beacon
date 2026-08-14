from __future__ import annotations

from pathlib import Path
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from live_opportunity_discovery.dashboard_service import DashboardService
from live_opportunity_discovery.router import build_live_opportunity_router


class FakeLiveOpportunityService:
    async def live(self, *, window_days: int = 7, limit: int = 100) -> dict[str, object]:
        return {"items": [], "count": 0, "window_days": window_days, "limit": limit}

    async def company(self, company_id: UUID) -> dict[str, object]:
        return {"company_id": str(company_id), "items": [], "timeline": [], "count": 0}

    async def timeline(self, company_id: UUID | None = None) -> dict[str, object]:
        return {"items": [], "count": 0, "company_id": str(company_id) if company_id else None}

    async def categories(self) -> dict[str, object]:
        return {"items": ["HIRING"], "count": 1}

    async def trending(self) -> dict[str, object]:
        return {"items": [], "count": 0}

    async def dashboard(self, *, window_days: int = 7) -> dict[str, object]:
        return {"items": [], "window_days": window_days}


def app() -> FastAPI:
    api = FastAPI()
    api.include_router(build_live_opportunity_router(lambda: FakeLiveOpportunityService()), prefix="/api/v1")
    return api


def test_live_opportunity_router_endpoints() -> None:
    client = TestClient(app())
    assert client.get("/api/v1/opportunities/live").json()["count"] == 0
    assert client.get("/api/v1/opportunities/company/00000000-0000-4000-8000-000000000001").status_code == 200
    assert client.get("/api/v1/opportunities/timeline").json()["count"] == 0
    assert client.get("/api/v1/opportunities/categories").json()["items"] == ["HIRING"]
    assert client.get("/api/v1/opportunities/trending").json()["count"] == 0
    assert client.get("/api/v1/opportunities/dashboard").json()["items"] == []


def test_dashboard_service_returns_operator_columns_and_filters() -> None:
    payload = DashboardService().build(
        [
            {
                "company_name": "OpenAI",
                "event_type": "Hiring Recruiters",
                "category": "HIRING",
                "buying_score": 91,
                "freshness_score": 100,
                "evidence_count": 3,
                "priority": "P0",
                "service_match": "Recruitment Automation",
                "event_timestamp": "2026-07-29T00:00:00+00:00",
            }
        ]
    )
    assert "Why today" not in payload["columns"]
    assert "Buying Score" in payload["columns"]
    assert "21_days" in payload["filters"]["windows"]
    assert payload["category_counts"]["HIRING"] == 1


def test_lode_migration_is_append_only_and_source_agnostic() -> None:
    migration = Path("apps/api/alembic/versions/20260728_0051_live_opportunity_discovery.py").read_text(
        encoding="utf-8"
    )
    assert 'revision = "20260728_0051"' in migration
    assert 'down_revision = "20260728_0050"' in migration
    assert '"live_opportunity_events"' in migration
    assert '"live_opportunity_evidence"' in migration
    assert "op.create_table" in migration
    assert "drop_table" in migration
