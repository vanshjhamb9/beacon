"""Integration: package facade + dashboard composition without DB."""

from uuid import uuid4

from revenue_hunter import RevenueHunterService, RevenueHunterInput


def test_service_facade_end_to_end() -> None:
    service = RevenueHunterService()
    decisions = [
        service.evaluate(
            RevenueHunterInput(
                company_id=uuid4(),
                company_name=f"Client {i}",
                industry="SaaS",
                country="USA",
                employee_count=150,
                funding_stage="Seed",
                pains=["manual workflows", "scaling issues"],
                signals=["hiring", "funding"],
                hiring_count=4,
                hiring_roles=["Ops Lead"],
                decision_makers=[{"name": "Pat", "role": "CEO"}],
                opportunity_score=75,
                verification_score=70,
                technologies=["HubSpot", "Zapier"],
            )
        )
        for i in range(5)
    ]
    dossiers = [d.dossier for d in decisions]
    dashboard = service.build_dashboard(dossiers)
    assert dashboard.generated_at is not None
    assert len(dashboard.top_25_companies) == 5
    for d in decisions:
        assert d.dossier.company_summary
        assert d.scoring_version == "rh-v1"
