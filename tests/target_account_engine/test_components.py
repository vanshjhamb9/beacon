from uuid import uuid4

from target_account_engine.budget.engine import BudgetEngine
from target_account_engine.buyer.accessibility import AccessibilityEngine
from target_account_engine.competition.engine import CompetitionEngine
from target_account_engine.hunter.mode import HunterMode
from target_account_engine.intent.engine import IntentEngine
from target_account_engine.models.types import TargetAccountDecision, TargetAccountInput, EngineScore, AccountTier
from target_account_engine.recommendations.improvements import ImprovementAdvisor
from target_account_engine.urgency.engine import UrgencyEngine


def _item(**overrides: object) -> TargetAccountInput:
    payload: dict[str, object] = {
        "company_id": uuid4(),
        "company_name": "Comp",
        "signals": ["funding", "hiring", "migration", "ai adoption"],
        "hiring_count": 9,
        "funding_days_ago": 14,
        "employee_count": 220,
        "funding_amount": 5_000_000,
        "country": "United States",
        "channels": ["email", "linkedin"],
        "decision_makers": [{"name": "Pat", "role": "CTO"}],
        "contacts": [{"email": "pat@example.com"}],
        "vendors": ["zendesk"],
        "technologies": ["zendesk"],
        "verification_score": 80,
    }
    payload.update(overrides)
    return TargetAccountInput(**payload)  # type: ignore[arg-type]


def test_intent_budget_urgency_accessibility_competition() -> None:
    item = _item()
    assert IntentEngine().score(item).score > 40
    budget = BudgetEngine().score(item)
    assert budget.band in {"medium", "large", "enterprise"}
    assert UrgencyEngine().score(item).score > 30
    assert AccessibilityEngine().score(item).score >= 40
    competition = CompetitionEngine().score(item)
    assert competition.score >= 40


def test_hunter_threshold_and_simulate() -> None:
    hunter = HunterMode(threshold=75)
    item = _item()
    assert hunter.should_trigger(80) is True
    job = hunter.plan(item, revenue_score=80)
    assert job is not None
    done = hunter.simulate_run(job, item)
    assert done.status.value == "completed"
    assert done.completed_tasks


def test_improvement_advisor_never_auto_trains() -> None:
    decision = TargetAccountDecision(
        company_id=uuid4(),
        company_name="Comp",
        fit=EngineScore(score=80, explanation="fit"),
        intent=EngineScore(score=70, explanation="intent"),
        budget=EngineScore(score=60, explanation="budget"),
        urgency=EngineScore(score=75, explanation="urgency"),
        accessibility=EngineScore(score=40, explanation="access"),
        competition=EngineScore(score=55, explanation="comp"),
        revenue_opportunity_score=72,
        tier=AccountTier.TOP,
        why_now="now",
        matched_icp_key="custom_ai_solutions",
        score_breakdown=[],
    )
    won = ImprovementAdvisor().from_outcome(decision, outcome="won")
    lost = ImprovementAdvisor().from_outcome(decision, outcome="lost")
    assert won and all(r.requires_approval for r in won)
    assert lost and all(r.requires_approval for r in lost)
