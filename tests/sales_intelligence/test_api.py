from app.main import app


def test_sales_intelligence_routes_registered() -> None:
    paths = {route.path for route in app.routes}
    assert "/api/v1/sales-intelligence/company/{company_id}" in paths
    assert "/api/v1/sales-intelligence/opportunity/{opportunity_id}" in paths
    assert "/api/v1/sales-intelligence/refresh/{company_id}" in paths
    assert "/api/v1/sales-intelligence/dashboard" in paths


def test_sales_intelligence_router_tags() -> None:
    tagged = [route for route in app.routes if getattr(route, "tags", None) and "sales-intelligence" in route.tags]
    assert len(tagged) >= 4
