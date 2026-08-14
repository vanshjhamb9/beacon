from app.main import app


def test_goap_routes_registered() -> None:
    paths = {route.path for route in app.routes}
    expected = [
        "/api/v1/opportunity-acquisition/dashboard",
        "/api/v1/opportunity-acquisition/connectors",
        "/api/v1/opportunity-acquisition/connectors/{connector_id}",
        "/api/v1/opportunity-acquisition/companies/{company_id}/graph",
        "/api/v1/opportunity-acquisition/website",
        "/api/v1/opportunity-acquisition/website/{company_key}",
        "/api/v1/opportunity-acquisition/technology",
        "/api/v1/opportunity-acquisition/technology/{company_key}",
        "/api/v1/opportunity-acquisition/funding",
        "/api/v1/opportunity-acquisition/hiring",
        "/api/v1/opportunity-acquisition/reviews",
        "/api/v1/opportunity-acquisition/community",
        "/api/v1/opportunity-acquisition/benchmarks",
        "/api/v1/opportunity-acquisition/freshness",
        "/api/v1/opportunity-acquisition/analytics",
        "/api/v1/opportunity-acquisition/daily-report",
        "/api/v1/opportunity-acquisition/refresh",
    ]
    for path in expected:
        assert path in paths


def test_goap_tag_present() -> None:
    tagged = [r for r in app.routes if getattr(r, "tags", None) and "opportunity-acquisition" in r.tags]
    assert len(tagged) >= 10
