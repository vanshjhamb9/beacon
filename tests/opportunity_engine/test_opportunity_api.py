from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_opportunity_routes_are_registered_in_openapi() -> None:
    app = create_app(
        Settings(
            environment="test",
            database_url="postgresql+asyncpg://beacon:beacon@localhost:5432/beacon",
            redis_url="redis://localhost:6379/15",
        )
    )

    paths = TestClient(app).get("/openapi.json").json()["paths"]

    assert "/api/v1/opportunities" in paths
    assert "/api/v1/opportunities/{opportunity_id}" in paths
    assert "/api/v1/opportunities/{opportunity_id}/history" in paths
    assert "/api/v1/opportunities/{opportunity_id}/evidence" in paths
    assert "/api/v1/opportunities/{opportunity_id}/timeline" in paths
    assert "/api/v1/opportunities/{opportunity_id}/recommendation" in paths
    assert "/api/v1/opportunities/statistics" in paths
