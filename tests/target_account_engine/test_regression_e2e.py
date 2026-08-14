from uuid import uuid4

from target_account_engine import TargetAccountEngineService, TargetAccountInput
from target_account_engine.models.types import AccountTier


def test_end_to_end_master_brain_flow() -> None:
    service = TargetAccountEngineService()
    item = TargetAccountInput(
        company_id=uuid4(),
        company_name="Launchpad Mobile",
        industry="Fintech",
        employee_count=75,
        funding_stage="seed",
        funding_days_ago=10,
        funding_amount=2_500_000,
        hiring_roles=["iOS Engineer", "Android Engineer", "Product Manager"],
        hiring_count=6,
        signals=["product launch", "funding", "mobile", "digital transformation", "expansion"],
        goals=["launching new product", "mobile app"],
        pains=["no mobile app"],
        decision_makers=[{"name": "Sam", "role": "Founder"}],
        channels=["email", "linkedin", "website"],
        contacts=[{"email": "sam@launchpad.example"}],
        verification_score=78,
        technologies=["react native"],
    )
    decision = service.evaluate(item)
    assert decision.matched_icp_key == "mobile_app_development"
    assert decision.tier in {AccountTier.TOP, AccountTier.MID, AccountTier.LOW}
    assert "pitch" in decision.why_now.lower() or "Mobile" in decision.why_now
    assert decision.evidence_chain
    if decision.revenue_opportunity_score > 75:
        job = service.start_hunter(item, revenue_score=decision.revenue_opportunity_score)
        assert job is not None
        assert job.status.value == "completed"
    summary = service.summarize([decision])
    assert summary["total"] == 1
