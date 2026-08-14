"""Regression — M4 does not redesign CIR/EROWD/CRE/GT locks."""

from __future__ import annotations

from company_intelligence import SCORING_VERSION as CIR
from company_resolution import SCORING_VERSION as CRE
from entity_resolution import SCORING_VERSION as EROWD
from ground_truth import LIVE_OUTREACH_ENABLED as GT_LIVE, PRODUCTION_SEND_LOCKED as GT_LOCK
from revenue_execution_validation import LIVE_OUTREACH_ENABLED, PRODUCTION_SEND_LOCKED, SCORING_VERSION


def test_versions():
    assert SCORING_VERSION == "rev-v1"
    assert CIR == "cir-v1"
    assert CRE == "cre-v1"
    assert EROWD == "erowd-v1"


def test_outreach_still_locked():
    assert LIVE_OUTREACH_ENABLED is False
    assert PRODUCTION_SEND_LOCKED is True
    assert GT_LIVE is False
    assert GT_LOCK is True


def test_no_new_intelligence_engines_imported_from_rev():
    import revenue_execution_validation as rev

    # Package should not re-export GPT/LLM helpers
    assert not hasattr(rev, "OpenAI")
    assert not hasattr(rev, "ChatCompletion")
