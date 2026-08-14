from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_version_endpoint_returns_application_metadata() -> None:
    app = create_app(
        Settings(
            app_name="Beacon Test API",
            app_version="0.1-test",
            environment="test",
            database_url="postgresql+asyncpg://beacon:beacon@localhost:5432/beacon",
            redis_url="redis://localhost:6379/15",
        )
    )

    response = TestClient(app).get("/api/v1/version", headers={"X-Request-ID": "trace-test"})

    assert response.status_code == 200
    assert response.json() == {
        "name": "Beacon Test API",
        "version": "0.1-test",
        "environment": "test",
    }
    assert response.headers["X-Request-ID"] == "trace-test"
