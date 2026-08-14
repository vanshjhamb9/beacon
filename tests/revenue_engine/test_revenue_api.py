from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_revenue_routes_are_registered_in_openapi() -> None:
    app = create_app(
        Settings(
            environment="test",
            database_url="postgresql+asyncpg://beacon:beacon@localhost:5432/beacon",
            redis_url="redis://localhost:6379/15",
        )
    )

    paths = TestClient(app).get("/openapi.json").json()["paths"]

    assert "/api/v1/revenue/opportunities" in paths
    assert "/api/v1/revenue/company/{company_id}" in paths
    assert "/api/v1/revenue/company/{company_id}/playbook" in paths
    assert "/api/v1/revenue/statistics" in paths
