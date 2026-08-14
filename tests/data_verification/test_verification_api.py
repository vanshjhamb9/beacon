from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_verification_routes_are_registered_in_openapi() -> None:
    app = create_app(
        Settings(
            environment="test",
            database_url="postgresql+asyncpg://beacon:beacon@localhost:5432/beacon",
            redis_url="redis://localhost:6379/15",
        )
    )

    paths = TestClient(app).get("/openapi.json").json()["paths"]

    assert "/api/v1/verification/company/{company_id}" in paths
    assert "/api/v1/verification/dashboard" in paths
    assert "/api/v1/verification/connectors" in paths
    assert "/api/v1/verification/profile/{verification_report_id}" in paths
    assert "/api/v1/verification/refresh/{entity_id}" in paths
