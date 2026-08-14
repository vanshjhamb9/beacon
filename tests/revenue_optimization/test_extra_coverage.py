import pytest

from revenue_optimization import RevenueOptimizationPipeline, RevenueOptimizationService
from revenue_optimization.models.types import ReplyCategory
from revenue_optimization.reply_intelligence.engine import ReplyIntelligenceV2Engine


@pytest.mark.parametrize("industry", ["SaaS", "Healthcare", "Manufacturing", "Construction", "FinTech"])
def test_industry_pipeline_runs(make_input, industry: str) -> None:
    d = RevenueOptimizationPipeline().process(make_input(4, industry=industry))
    assert d.industries
    assert d.scoring_version == "roip-v1"


@pytest.mark.parametrize(
    "offer",
    [
        "Website Development",
        "Mobile Apps",
        "Custom SaaS",
        "AI Automation",
        "AI Chatbots",
        "Internal AI",
        "CRM",
        "ERP",
        "Workflow Automation",
        "Data Platform",
        "Dashboards",
        "Integrations",
    ],
)
def test_offer_variants(make_input, offer: str) -> None:
    d = RevenueOptimizationPipeline().process(make_input(3, offer=offer, closed_won=True, deal_value=12_000))
    assert any(o.offer == offer for o in d.offers)


@pytest.mark.parametrize(
    "cta",
    [
        "book_meeting",
        "free_consultation",
        "ai_audit",
        "reply_back",
        "quick_question",
        "15_min_discovery",
        "download_guide",
        "watch_demo",
    ],
)
def test_cta_variants(make_input, cta: str) -> None:
    d = RevenueOptimizationPipeline().process(make_input(2, cta=cta))
    assert any(c.cta == cta for c in d.ctas)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("interested in this", ReplyCategory.INTERESTED),
        ("send more info please", ReplyCategory.NEED_MORE_INFO),
        ("budget is a concern", ReplyCategory.BUDGET_ISSUE),
        ("next quarter maybe", ReplyCategory.TIMING_ISSUE),
        ("already using a tool", ReplyCategory.ALREADY_USING_SOLUTION),
        ("comparing vs competitor", ReplyCategory.COMPETITOR),
        ("will discuss internally", ReplyCategory.INTERNAL_DISCUSSION),
        ("decision pending under review", ReplyCategory.DECISION_PENDING),
        ("not interested remove me", ReplyCategory.NEGATIVE),
        ("thanks appreciate this", ReplyCategory.POSITIVE),
        ("schedule a calendly meet", ReplyCategory.MEETING_REQUESTED),
    ],
)
def test_reply_pattern_matrix(make_event, text: str, expected: ReplyCategory) -> None:
    rows = ReplyIntelligenceV2Engine().analyze([make_event(replied=True, reply_text=text)])
    assert rows[0].category == expected


@pytest.mark.parametrize("i", range(40))
def test_batch_deterministic(make_input, i: int) -> None:
    data = make_input(2, subject=f"Subj {i % 7}", industry=["SaaS", "Healthcare"][i % 2])
    a = RevenueOptimizationService().evaluate(data)
    b = RevenueOptimizationService().evaluate(data)
    assert a.email_metrics.open_rate == b.email_metrics.open_rate
    assert a.founder.pipeline_health == b.founder.pipeline_health
    assert len(a.benchmarks) == len(b.benchmarks)


@pytest.mark.parametrize("channel", ["email", "whatsapp"])
def test_channel_founder_counts(make_input, channel: str) -> None:
    d = RevenueOptimizationPipeline().process(make_input(3, channel=channel))
    if channel == "email":
        assert d.founder.emails_sent >= 1
    else:
        assert d.founder.whatsapp_messages >= 1


@pytest.mark.parametrize("n", [0, 1, 5, 20])
def test_empty_and_small_batches(make_input, n: int) -> None:
    if n == 0:
        from revenue_optimization.models.types import ROIPInput

        d = RevenueOptimizationPipeline().process(ROIPInput(events=[]))
    else:
        d = RevenueOptimizationPipeline().process(make_input(n))
    assert d.scoring_version == "roip-v1"
    assert d.learning.modifies_production is False


@pytest.mark.parametrize("weekday", [0, 1, 2, 3, 4])
def test_followup_weekday_modes(make_input, weekday: int) -> None:
    d = RevenueOptimizationPipeline().process(make_input(4, open_weekday=weekday, replied=True))
    assert d.followup.best_day == weekday


@pytest.mark.parametrize("hour", [8, 9, 10, 14, 16])
def test_followup_hour_modes(make_input, hour: int) -> None:
    d = RevenueOptimizationPipeline().process(make_input(3, open_hour=hour, replied=True))
    assert d.followup.best_hour == hour


@pytest.mark.parametrize("delay", [2.0, 3.0, 4.0, 5.0])
def test_followup_delay_recommendation(make_input, delay: float) -> None:
    d = RevenueOptimizationPipeline().process(make_input(4, delay_days=delay, industry="SaaS", replied=True))
    assert d.recommendations
    assert all(r.evidence for r in d.recommendations)
