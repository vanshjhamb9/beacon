"""HTTP contract definitions for Outcome Intelligence (implemented by apps/api)."""

OUTCOME_API_ROUTES: dict[str, str] = {
    "dashboard": "GET /api/v1/outcomes/dashboard",
    "company": "GET /api/v1/outcomes/company/{id}",
    "update": "POST /api/v1/outcomes/update",
    "analytics": "GET /api/v1/outcomes/analytics",
}
