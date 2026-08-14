"""Tests for ProposalTracker."""

from __future__ import annotations

import pytest

from validation_engine import PROPOSAL_STATUSES
from validation_engine.proposal_tracker import ProposalTracker


class TestProposalTrackerRecordProposal:
    def test_record_valid_proposal(self, proposal_tracker: ProposalTracker) -> None:
        event = proposal_tracker.record_proposal("company_1", "sent")
        assert event.company_id == "company_1"
        assert event.status == "sent"

    def test_record_invalid_status_raises(self, proposal_tracker: ProposalTracker) -> None:
        with pytest.raises(ValueError, match="Invalid status"):
            proposal_tracker.record_proposal("company_1", "invalid")

    def test_record_all_statuses(self, proposal_tracker: ProposalTracker) -> None:
        for status in PROPOSAL_STATUSES:
            event = proposal_tracker.record_proposal("company_1", status)
            assert event.status == status

    def test_record_with_value(self, proposal_tracker: ProposalTracker) -> None:
        event = proposal_tracker.record_proposal("company_1", "sent", value=50000.0)
        assert event.value == 50000.0


class TestProposalTrackerGetProposalsForCompany:
    def test_get_empty_proposals(self, proposal_tracker: ProposalTracker) -> None:
        proposals = proposal_tracker.get_proposals_for_company("nonexistent")
        assert proposals == []

    def test_get_proposals_filtered(self, proposal_tracker: ProposalTracker) -> None:
        proposal_tracker.record_proposal("company_1", "sent")
        proposal_tracker.record_proposal("company_1", "accepted")
        proposal_tracker.record_proposal("company_2", "sent")
        proposals = proposal_tracker.get_proposals_for_company("company_1")
        assert len(proposals) == 2


class TestProposalTrackerFilteredViews:
    def test_sent_proposals(self, proposal_tracker: ProposalTracker) -> None:
        proposal_tracker.record_proposal("company_1", "sent")
        proposal_tracker.record_proposal("company_2", "accepted")
        sent = proposal_tracker.get_sent_proposals()
        assert len(sent) == 1

    def test_accepted_proposals(self, proposal_tracker: ProposalTracker) -> None:
        proposal_tracker.record_proposal("company_1", "accepted")
        accepted = proposal_tracker.get_accepted_proposals()
        assert len(accepted) == 1

    def test_rejected_proposals(self, proposal_tracker: ProposalTracker) -> None:
        proposal_tracker.record_proposal("company_1", "rejected")
        rejected = proposal_tracker.get_rejected_proposals()
        assert len(rejected) == 1

    def test_expired_proposals(self, proposal_tracker: ProposalTracker) -> None:
        proposal_tracker.record_proposal("company_1", "expired")
        expired = proposal_tracker.get_expired_proposals()
        assert len(expired) == 1


class TestProposalTrackerRates:
    def test_proposal_rate_empty(self, proposal_tracker: ProposalTracker) -> None:
        rate = proposal_tracker.get_proposal_rate()
        assert rate == 0.0

    def test_proposal_rate_calculated(self, proposal_tracker: ProposalTracker) -> None:
        proposal_tracker.record_proposal("company_1", "sent")
        proposal_tracker.record_proposal("company_2", "created")
        rate = proposal_tracker.get_proposal_rate()
        assert rate == 50.0

    def test_acceptance_rate_empty(self, proposal_tracker: ProposalTracker) -> None:
        rate = proposal_tracker.get_acceptance_rate()
        assert rate == 0.0

    def test_acceptance_rate_calculated(self, proposal_tracker: ProposalTracker) -> None:
        proposal_tracker.record_proposal("company_1", "sent")
        proposal_tracker.record_proposal("company_1", "accepted")
        proposal_tracker.record_proposal("company_2", "sent")
        proposal_tracker.record_proposal("company_2", "rejected")
        rate = proposal_tracker.get_acceptance_rate()
        assert rate == 50.0


class TestProposalTrackerTotalValue:
    def test_total_value_empty(self, proposal_tracker: ProposalTracker) -> None:
        total = proposal_tracker.get_total_proposal_value()
        assert total == 0.0

    def test_total_value_calculated(self, proposal_tracker: ProposalTracker) -> None:
        proposal_tracker.record_proposal("company_1", "sent", value=50000.0)
        proposal_tracker.record_proposal("company_2", "sent", value=75000.0)
        total = proposal_tracker.get_total_proposal_value()
        assert total == 125000.0


class TestProposalTrackerStatusCounts:
    def test_status_counts(self, proposal_tracker: ProposalTracker) -> None:
        proposal_tracker.record_proposal("company_1", "sent")
        proposal_tracker.record_proposal("company_2", "sent")
        proposal_tracker.record_proposal("company_3", "accepted")
        counts = proposal_tracker.get_status_counts()
        assert counts["sent"] == 2
        assert counts["accepted"] == 1
