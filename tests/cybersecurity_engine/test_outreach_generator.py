"""Tests for cybersecurity_engine.outreach_generator."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "packages"))

from cybersecurity_engine.models import (
    CybersecurityOpportunity, OpportunityPriority, OutreachPreparation,
)
from cybersecurity_engine.outreach_generator import OutreachMessageGenerator


@pytest.fixture
def generator():
    return OutreachMessageGenerator(sender_name="Test Team", sender_company="TestSec")


class TestOutreachMessageGenerator:
    def test_generate_p0_message(self, sample_opportunity, generator):
        prep = generator.generate(sample_opportunity)
        assert "Alex" in prep.personalized_message
        assert "TestSec" in prep.personalized_message or "Test Team" in prep.personalized_message
        assert len(prep.personalized_message) > 50

    def test_generate_subject_p0(self, sample_opportunity, generator):
        prep = generator.generate(sample_opportunity)
        assert "Re:" in prep.outreach_angle
        assert "TestCo" in prep.outreach_angle

    def test_generate_follow_ups(self, sample_opportunity, generator):
        prep = generator.generate(sample_opportunity)
        assert len(prep.follow_up_sequence) == 3
        assert "3 days" in prep.follow_up_sequence[0]
        assert "7 days" in prep.follow_up_sequence[1]
        assert "14 days" in prep.follow_up_sequence[2]

    def test_follow_up_contains_buyer(self, sample_opportunity, generator):
        prep = generator.generate(sample_opportunity)
        for fu in prep.follow_up_sequence:
            assert "Test Team" in fu

    def test_value_proposition_p0(self, sample_opportunity, generator):
        prep = generator.generate(sample_opportunity)
        assert len(prep.personalized_message) > 50

    def test_p1_problem_first(self, sample_opportunity, generator):
        sample_opportunity.priority = OpportunityPriority.P1
        sample_opportunity.outreach_preparation.outreach_angle = "problem_first"
        prep = generator.generate(sample_opportunity)
        assert len(prep.personalized_message) > 50

    def test_p2_value_proposition(self, sample_opportunity, generator):
        sample_opportunity.priority = OpportunityPriority.P2
        sample_opportunity.outreach_preparation.outreach_angle = "value_proposition"
        prep = generator.generate(sample_opportunity)
        assert len(prep.personalized_message) > 50
