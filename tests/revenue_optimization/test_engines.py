from revenue_optimization.cta_intelligence.engine import CTAIntelligenceEngine, FollowupIntelligenceEngine
from revenue_optimization.email_performance.engine import EmailPerformanceEngine, SubjectLineIntelligenceEngine
from revenue_optimization.industry_conversion.engine import (
    CaseStudyIntelligenceEngine,
    FounderPerformanceEngine,
    IndustryConversionEngine,
    OfferIntelligenceEngine,
)
from revenue_optimization.models.types import CTAType, OfferType, ReplyCategory
from revenue_optimization.reply_intelligence.engine import (
    OptimizationRecommendationEngine,
    ReplyIntelligenceV2Engine,
    RevenueBenchmarkEngine,
    RevenueLearningEngine,
)


def test_email_performance_counts(make_event) -> None:
    events = [
        make_event(delivered=True, opened=True, open_count=3, bounced=False),
        make_event(delivered=True, opened=False, open_count=0, replied=False, reply_text=""),
        make_event(delivered=False, opened=False, open_count=0, bounced=True, replied=False, reply_text=""),
    ]
    m = EmailPerformanceEngine().analyze(events)
    assert m.delivered == 2
    assert m.opened == 1
    assert m.multiple_opens == 1
    assert m.bounce == 1
    assert m.evidence


def test_subject_ranking(make_event) -> None:
    events = [
        make_event(subject="A", opened=True, replied=True, closed_won=True, deal_value=10_000),
        make_event(subject="A", opened=True, replied=False, closed_won=False, deal_value=0),
        make_event(subject="B", opened=False, replied=False, closed_won=False, deal_value=0),
    ]
    rows = SubjectLineIntelligenceEngine().rank(events)
    assert rows[0].rank == 1
    assert rows[0].subject in {"A", "B"}


def test_cta_scores(make_event) -> None:
    events = [make_event(cta=CTAType.AI_AUDIT.value, calendly_clicks=2, meeting_booked=True, closed_won=True)]
    rows = CTAIntelligenceEngine().analyze(events)
    assert rows
    assert rows[0].score >= 0


def test_followup_patterns(make_event) -> None:
    events = [
        make_event(open_weekday=1, open_hour=9, delay_days=4, followup_number=3, sequence_length=5, replied=True),
        make_event(open_weekday=1, open_hour=9, delay_days=4, followup_number=3, sequence_length=5, replied=True),
    ]
    p = FollowupIntelligenceEngine().analyze(events)
    assert p.best_day == 1
    assert p.best_hour == 9
    assert p.evidence


def test_industry_metrics(make_event) -> None:
    events = [make_event(industry="Manufacturing", closed_won=True), make_event(industry="Healthcare", closed_won=False)]
    rows = IndustryConversionEngine().analyze(events)
    assert {r.industry for r in rows} >= {"Manufacturing", "Healthcare"}


def test_founder_metrics(make_event) -> None:
    events = [
        make_event(channel="email"),
        make_event(channel="whatsapp", replied=True, meeting_booked=True),
    ]
    m = FounderPerformanceEngine().analyze(events)
    assert m.emails_sent >= 1
    assert m.whatsapp_messages >= 1
    assert m.evidence


def test_offer_metrics(make_event) -> None:
    events = [make_event(offer=OfferType.AI_AUTOMATION.value, closed_won=True, deal_value=20_000)]
    rows = OfferIntelligenceEngine().analyze(events)
    assert rows[0].wins >= 1
    assert rows[0].revenue >= 20_000


def test_case_study_recommend(make_event) -> None:
    events = [make_event(industry="SaaS", pain_points=["automation"], technology=["python"])]
    assets = [{"asset_id": "p1", "asset_type": "portfolio", "title": "SaaS build", "industry": "SaaS"}]
    rows = CaseStudyIntelligenceEngine().recommend(events, assets)
    assert rows
    assert rows[0].evidence


def test_reply_categories(make_event) -> None:
    events = [
        make_event(replied=True, reply_text="Please book a call on calendly"),
        make_event(replied=True, reply_text="budget is too expensive"),
        make_event(replied=False, reply_text="", delivered=True),
    ]
    rows = ReplyIntelligenceV2Engine().analyze(events)
    cats = {r.category for r in rows}
    assert ReplyCategory.MEETING_REQUESTED in cats
    assert ReplyCategory.BUDGET_ISSUE in cats
    assert ReplyCategory.NO_RESPONSE in cats


def test_learning_never_mutates(make_event) -> None:
    insight = RevenueLearningEngine().learn(
        [make_event(closed_won=True), make_event(closed_lost=True, reply_text="budget later")]
    )
    assert insight.modifies_production is False
    assert insight.why_won or insight.why_lost


def test_benchmarks_periods(make_input) -> None:
    data = make_input(10)
    benches = RevenueBenchmarkEngine().benchmark(list(data.events), list(data.previous_period_events))
    assert len(benches) == 5
    assert all(b.evidence for b in benches)


def test_recommendations_require_approval(make_input) -> None:
    data = make_input(5, industry="Manufacturing", delay_days=4.0)
    industries = IndustryConversionEngine().analyze(list(data.events))
    offers = OfferIntelligenceEngine().analyze(list(data.events))
    followup = FollowupIntelligenceEngine().analyze(list(data.events))
    recs = OptimizationRecommendationEngine().generate(
        followup_delay=followup.best_delay_days,
        industries=industries,
        offers=offers,
        followup_day=1,
        channels_by_industry={"Construction": "whatsapp"},
    )
    assert recs
    assert all(r.requires_founder_approval and not r.modifies_production and r.evidence for r in recs)
