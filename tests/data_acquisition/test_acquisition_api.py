from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_acquisition_routes_are_registered_in_openapi() -> None:
    app = create_app(
        Settings(
            environment="test",
            database_url="postgresql+asyncpg://beacon:beacon@localhost:5432/beacon",
            redis_url="redis://localhost:6379/15",
        )
    )
    paths = TestClient(app).get("/openapi.json").json()["paths"]
    assert "/api/v1/acquisition/dashboard" in paths
    assert "/api/v1/acquisition/audit" in paths
    assert "/api/v1/acquisition/benchmarks" in paths
    assert "/api/v1/acquisition/alerts" in paths
    assert "/api/v1/acquisition/reports/daily" in paths
