from app.main import app


def test_roip_routes_registered() -> None:
    paths = {route.path for route in app.routes}
    for path in [
        "/api/v1/revenue-optimization/dashboard",
        "/api/v1/revenue-optimization/company/{company_id}",
        "/api/v1/revenue-optimization/campaign/{campaign_id}",
        "/api/v1/revenue-optimization/founder",
        "/api/v1/revenue-optimization/industry",
        "/api/v1/revenue-optimization/offers",
        "/api/v1/revenue-optimization/recommendations",
        "/api/v1/revenue-optimization/benchmarks",
        "/api/v1/revenue-optimization/learning",
        "/api/v1/revenue-optimization/replies",
        "/api/v1/revenue-optimization/search",
        "/api/v1/revenue-optimization/refresh",
    ]:
        assert path in paths


def test_roip_tags() -> None:
    tagged = [r for r in app.routes if getattr(r, "tags", None) and "revenue-optimization" in r.tags]
    assert len(tagged) >= 10
