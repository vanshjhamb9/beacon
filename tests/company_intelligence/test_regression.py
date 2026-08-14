"""Regression — CIR must not break CRE / EROWD / SRE / GT."""

from __future__ import annotations

from company_intelligence import SCORING_VERSION as CIR
from company_resolution import SCORING_VERSION as CRE
from entity_resolution import SCORING_VERSION as EROWD
from ground_truth import SCORING_VERSION as GT
from sales_readiness import SCORING_VERSION as SRE


def test_versions_intact():
    assert CIR == "cir-v1"
    assert CRE == "cre-v1"
    assert EROWD == "erowd-v1"
    assert GT == "alpha-plus-v1"
    assert SRE  # any non-empty


def test_pipelines_import():
    from company_intelligence.pipelines.engine import CirPipeline
    from company_resolution.pipelines.engine import CompanyResolutionPipeline
    from entity_resolution.pipelines.engine import ErowdPipeline
    from ground_truth.pipelines.engine import GroundTruthPipeline
    from sales_readiness.pipelines.engine import SalesReadinessPipeline

    assert CirPipeline
    assert CompanyResolutionPipeline
    assert ErowdPipeline
    assert GroundTruthPipeline
    assert SalesReadinessPipeline


def test_erowd_still_rejects_without_website():
    from entity_resolution.pipelines.engine import ErowdPipeline

    snap = ErowdPipeline().evaluate(
        {
            "signal_id": "reg",
            "title": "noise",
            "body": "x",
            "url": "https://news.ycombinator.com/item?id=1",
            "source": "hacker_news",
        }
    )
    assert not snap.admission.allow_create_company


def test_cre_still_imports_identity_threshold():
    from company_resolution.identity_confidence.engine import IDENTITY_THRESHOLD

    assert IDENTITY_THRESHOLD == 90.0


def test_gt_founder_queue_without_cir_unchanged():
    from ground_truth.founder_queue.engine import GtFounderQueueEngine
    from ground_truth.models.types import (
        FounderQueueItem,
        GtSnapshot,
        GtVerdict,
        ProductionLockResult,
        TruthQuestions,
    )

    item = FounderQueueItem(
        company_id="g1",
        company="Good",
        reason="hiring",
        evidence="e",
        contact="a",
        email="a@x.com",
        phone="UNKNOWN",
        decision_maker="a",
        service="AI",
        estimated_deal="$40k",
        next_step="email",
        open_profile="/x",
        approve=False,
        trust=80,
        score=80,
    )
    snap = GtSnapshot(
        company_id="g1",
        company_name="Good",
        verdict=GtVerdict.SALES_READY,
        questions=TruthQuestions(all_answered=True),
        founder_item=item,
        production_lock=ProductionLockResult(unlocked=True),
        trust=80,
        readiness=80,
        evidence=[],
    )
    # No cir_classification evidence → still eligible
    out = GtFounderQueueEngine().top10([snap])
    assert len(out) == 1


def test_gt_founder_queue_filters_cir_rejected():
    from ground_truth.founder_queue.engine import GtFounderQueueEngine
    from ground_truth.models.types import (
        FounderQueueItem,
        GtSnapshot,
        GtVerdict,
        ProductionLockResult,
        TruthQuestions,
    )

    item = FounderQueueItem(company_id="g2", company="Bad", reason="x", evidence="e", contact="a", email="a@x.com")
    snap = GtSnapshot(
        company_id="g2",
        company_name="Bad",
        verdict=GtVerdict.SALES_READY,
        questions=TruthQuestions(all_answered=True),
        founder_item=item,
        production_lock=ProductionLockResult(unlocked=True),
        trust=80,
        readiness=80,
        evidence=["cir_classification:Observed"],
    )
    assert GtFounderQueueEngine().top10([snap]) == []
