from app.main import app


def test_aip_routes_registered() -> None:
    paths = {route.path for route in app.routes}
    for path in [
        "/api/v1/account-intelligence/dashboard",
        "/api/v1/account-intelligence/search",
        "/api/v1/account-intelligence/company/{company_id}",
        "/api/v1/account-intelligence/company/{company_id}/contacts",
        "/api/v1/account-intelligence/company/{company_id}/technology",
        "/api/v1/account-intelligence/company/{company_id}/website",
        "/api/v1/account-intelligence/company/{company_id}/business",
        "/api/v1/account-intelligence/company/{company_id}/readiness",
        "/api/v1/account-intelligence/company/{company_id}/relationship",
        "/api/v1/account-intelligence/company/{company_id}/timeline",
        "/api/v1/account-intelligence/company/{company_id}/verification",
        "/api/v1/account-intelligence/refresh",
        "/api/v1/account-intelligence/refresh/{company_id}",
    ]:
        assert path in paths


def test_aip_tags() -> None:
    tagged = [r for r in app.routes if getattr(r, "tags", None) and "account-intelligence" in r.tags]
    assert len(tagged) >= 10
